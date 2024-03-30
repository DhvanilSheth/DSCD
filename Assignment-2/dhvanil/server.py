import grpc
import raft_pb2
import raft_pb2_grpc
import random
import time
import threading
import os
import sys
from concurrent import futures

# Setting constants 
HEARTBEAT_INTERVAL = 1.0
ELECTION_TIMEOUT_MIN = 5.0
ELECTION_TIMEOUT_MAX = 10.0
LEASE_DURATION = 10

# States of the Raft node
FOLLOWER = 0
CANDIDATE = 1
LEADER = 2

class Raft(raft_pb2_grpc.RaftServicer):
    def __init__(self, node_id, node_addresses):
        self.node_id = node_id
        self.node_addresses = node_addresses
        self.state = FOLLOWER
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.commit_length = 0
        self.current_leader = None
        self.votes_received = set()
        self.sent_length = {}
        self.acked_length = {}
        self.election_timer = None
        self.heartbeat_timer = None
        self.lease_timer = None
        self.old_leader_lease_timeout = 0
        self.heartbeat_success_count = set()
        self.lease_start_time = 0
        self.data_store = {}
        self.load_state()
        self.create_dump_file()

    # Create and write functions to dump info
    def create_dump_file(self):
        """Create the dump file for the node."""
        os.makedirs(f"logs_node_{self.node_id}", exist_ok=True)
        try:
            self.dump_file = open(f"logs_node_{self.node_id}/dump.txt", "a")
        except FileNotFoundError:
            self.dump_file = open(f"logs_node_{self.node_id}/dump.txt", "w")

    def write_to_dump_file(self, message):
        """Write a message to the dump file with a timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.dump_file.write(log_message + "\n")
        self.dump_file.flush()

    # Store and Load state functions to persist the logs and metadata
    def load_state(self):
        """Load the state from disk to recover the logs and metadata"""
        log_file_path = f"logs_node_{self.node_id}/logs.txt"
        metadata_file_path = f"logs_node_{self.node_id}/metadata.txt"

        try:
            with open(metadata_file_path, "r") as metadata_file:
                self.commit_length = int(metadata_file.readline().strip())
                self.current_term = int(metadata_file.readline().strip())
                self.voted_for = metadata_file.readline().strip() or None

            with open(log_file_path, "r") as log_file:
                for line in log_file:
                    parts = line.strip().split(" ")
                    if parts[0] == "NO-OP":
                        term = int(parts[1])
                        self.log.append(raft_pb2.LogEntry(operation="NO-OP", term=term))
                    elif parts[0] == "SET":
                        key, value, term = parts[1], parts[2], int(parts[3])
                        self.log.append(raft_pb2.LogEntry(operation="SET", key=key, value=value, term=term))
                        if len(self.log) <= self.commit_length:
                            self.data_store[key] = value
        except FileNotFoundError:
            pass

    def store_state(self):
        """Save the current state on disk to persist the logs and metadata"""
        log_file_path = f"logs_node_{self.node_id}/logs.txt"
        metadata_file_path = f"logs_node_{self.node_id}/metadata.txt"

        os.makedirs(f"logs_node_{self.node_id}", exist_ok=True)

        with open(log_file_path, "w") as log_file:
            for entry in self.log:
                if entry.operation == "NO-OP":
                    log_file.write(f"NO-OP {entry.term}\n")
                elif entry.operation == "SET":
                    log_file.write(f"SET {entry.key} {entry.value} {entry.term}\n")

        with open(metadata_file_path, "w") as metadata_file:
            metadata_file.write(f"{self.commit_length}\n")
            metadata_file.write(f"{self.current_term}\n")
            metadata_file.write(f"{self.voted_for or ''}\n")

    # Start Timer functions for election, heartbeat and lease
    # Threading.Timer is used to start a timer that will run a function after a specified number of seconds
    def start_election_timer(self):
        """Start the election timer with a random duration"""
        election_timeout = random.uniform(ELECTION_TIMEOUT_MIN, ELECTION_TIMEOUT_MAX)
        self.election_timer = threading.Timer(election_timeout, self.start_election)
        self.election_timer.start()

    def start_heartbeat_timer(self):
        """Start the heartbeat timer with a fixed interval"""
        self.heartbeat_timer = threading.Timer(HEARTBEAT_INTERVAL, self.send_heartbeats)
        self.heartbeat_timer.start()

    def start_lease_timer(self):
        """Start the lease timer with a fixed duration"""
        self.lease_start_time = time.time()
        self.lease_timer = threading.Timer(LEASE_DURATION, self.lease_timeout)
        self.lease_timer.start()

    # Cancel Timer functions for election, heartbeat and lease
    def cancel_election_timer(self):
        """Cancel the election timer if it is active"""
        if self.election_timer:
            self.election_timer.cancel()

    def cancel_heartbeat_timer(self):
        """Cancel the heartbeat timer if it is active"""
        if self.heartbeat_timer:
            self.heartbeat_timer.cancel()

    def cancel_lease_timer(self):
        """Cancel the lease timer if it is active"""
        if self.lease_timer:
            self.lease_timer.cancel()

    # Start and Check Election functions for the election process
    def check_election_result(self):
        """Check the result of the election after the election timer expires"""
        if len(self.votes_received) < (len(self.node_addresses) // 2) + 1:
            self.start_election_timer()
        else:
            self.become_leader()

    def start_election(self):
        """Start the election process by incrementing the term and requesting votes from other nodes"""
        self.write_to_dump_file(f"Node {self.node_id} election timeout. Starting new election.")
        self.state = CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.votes_received = {self.node_id}

        last_term = 0
        if self.log:
            last_term = self.log[-1].term
        self.store_state()

        threads = []
        for node_id, _ in self.node_addresses.items():
            if node_id == self.node_id:
                continue
            else:
                thread = self.request_vote_async(node_id, last_term)
                threads.append(thread)

        timer = threading.Timer(0.1, self.check_election_result)
        timer.start()
       
    # Create, Send and Request Vote functions for the election process   
    def create_vote_request(self, node_id, last_term):
        """Create a vote request for a specific node"""
        channel = grpc.insecure_channel(self.node_addresses[node_id])
        stub = raft_pb2_grpc.RaftStub(channel)

        request = raft_pb2.RequestVoteArgs(
            term=self.current_term,
            candidate_id=self.node_id,
            last_log_index=len(self.log),
            last_log_term=last_term
        )
        return stub, request, channel

    def send_vote_request(self, stub, request, node_id, channel):
        """Send a vote request to a specific node"""
        try:
            response = stub.RequestVote(request, timeout=1)

            if response.vote_granted:
                self.votes_received.add(node_id)

                remaining_lease_duration = self.old_leader_lease_timeout - (time.time() - self.lease_start_time)
                if remaining_lease_duration < 0:
                    remaining_lease_duration = 0
                self.old_leader_lease_timeout = max(remaining_lease_duration, response.old_leader_lease_timeout)
                    
        except grpc.RpcError as e:
            # Handle any errors that occur during the RPC
            self.write_to_dump_file(f"Error occurred while sending RPC to Node {node_id}.")
        finally:
            channel.close()

    def request_vote_async(self, node_id, last_term):
        """Start the request_vote_task in a separate thread and return the thread object"""
        stub, request, channel = self.create_vote_request(node_id, last_term)
        thread = threading.Thread(target=self.send_vote_request, args=(stub, request, node_id, channel))
        thread.start()
        return thread

    # Become Leader function to handle the leader election process
    def become_leader(self):
        """Handle the leader election process after receiving votes from a majority of nodes"""
        self.write_to_dump_file(f"Node {self.node_id} is the leader for term {self.current_term}.")
        self.state = LEADER
        self.current_leader = self.node_id
        self.votes_received = set()
        self.sent_length = {node_id: len(self.log) for node_id in self.node_addresses}
        self.acked_length = {node_id: 0 for node_id in self.node_addresses}
        self.cancel_election_timer()

        self.write_to_dump_file("Waiting for Old Leader Lease to timeout.")
        time.sleep(self.old_leader_lease_timeout)

        self.start_lease_timer()
        self.append_no_op_entry()
        self.send_heartbeats()

    def lease_timeout(self):
        """Handle the case when the leader lease expires without renewing the lease"""
        self.write_to_dump_file(f"Leader {self.node_id} lease renewal failed. Stepping Down.")
        self.step_down()

    def step_down(self):
        """Step down from the leader role and become a follower"""
        self.write_to_dump_file(f"{self.node_id} Stepping down")
        self.state = FOLLOWER
        self.current_leader = None
        self.votes_received = set()
        self.sent_length = {}
        self.acked_length = {}
        self.cancel_heartbeat_timer()
        self.cancel_lease_timer()
        self.cancel_election_timer()
        self.start_election_timer()

    def append_no_op_entry(self):
        """Append a NO-OP entry to the log to maintain the leader lease"""
        self.log.append(raft_pb2.LogEntry(operation="NO-OP", term=self.current_term))
        self.store_state()

    # Create, Send and Heartbeat functions for the leader to send heartbeats to followers
    def create_heartbeat(self):
        """Create a heartbeat for all the followers"""
        threads = []
        self.heartbeat_success_nodes = set()
        for node_id, node_address in self.node_addresses.items():
            if node_id != self.node_id:
                thread = self.replicate_log_async(node_id)
                threads.append(thread)
        return threads

    def send_heartbeat(self):
        """Send the heartbeat to all the followers and check the lease renewal"""
        def check_lease_renewal():
            if len(self.heartbeat_success_nodes) < (len(self.node_addresses) // 2):
                self.write_to_dump_file(f"Leader {self.node_id} failed to renew lease. Stepping down.")
                self.step_down()

        remaining_lease_time = self.lease_timer.interval - (time.time() - self.lease_start_time)
        timer = threading.Timer(remaining_lease_time, check_lease_renewal)
        timer.start()
        self.start_heartbeat_timer()

    def send_heartbeats(self):
        """Using the create_heartbeat and send_heartbeat functions"""
        self.write_to_dump_file(f"Leader {self.node_id} sending heartbeat & Renewing Lease")
        self.lease_timer.cancel()
        self.start_lease_timer()
        self.create_heartbeat()
        self.send_heartbeat()
        
    # Create, Send and Replicate Log functions for the leader to replicate logs to followers    
    def create_log_replication(self, follower_id):
        """Create a log replication for a specific follower"""
        channel = grpc.insecure_channel(self.node_addresses[follower_id])
        stub = raft_pb2_grpc.RaftStub(channel)
        prefix_length = self.sent_length.get(follower_id, 0)
        suffix = self.log[prefix_length:]
        prefix_term = 0
        if prefix_length > 0:
            prefix_term = self.log[prefix_length - 1].term
        request = raft_pb2.AppendEntriesArgs(
            term=self.current_term,
            leader_id=self.node_id,
            prev_log_index=prefix_length,
            prev_log_term=prefix_term,
            entries=suffix,
            leader_commit=self.commit_length,
            lease_duration=LEASE_DURATION
        )
        return stub, request, prefix_length, suffix, channel

    def send_log_replication(self, stub, request, follower_id, prefix_length, suffix, channel):
        """Send a log replication to a specific follower"""
        try:
            response = stub.AppendEntries(request, timeout=1)
            if response.success:
                self.sent_length[follower_id] = prefix_length + len(suffix)
                self.acked_length[follower_id] = prefix_length + len(suffix)
                self.commit_log_entries()
                self.heartbeat_success_nodes.add(follower_id)
            else:
                self.sent_length[follower_id] = max(0, self.sent_length.get(follower_id, 0) - 1)
                self.replicate_log_async(follower_id)
        except grpc.RpcError as e:
            self.write_to_dump_file(f"Error occurred while sending RPC to Node {follower_id}.")
        finally:
            channel.close()

    def replicate_log_async(self, follower_id):
        """Start the replicate_log_task in a separate thread and return the thread object"""
        stub, request, prefix_length, suffix, channel = self.create_log_replication(follower_id)
        thread = threading.Thread(target=self.send_log_replication, args=(stub, request, follower_id, prefix_length, suffix, channel))
        thread.start()
        return thread
    
    # Commit Log Entries function to commit the log entries
    def commit_log_entries(self):
        """Commit log entries if a majority of nodes have replicated them"""
        min_acks = len(self.node_addresses) // 2
        ready_entries = [index for index in range(1, len(self.log) + 1)
                         if len([node_id for node_id, acked_length in self.acked_length.items()
                                 if acked_length >= index]) >= min_acks]

        if ready_entries:
            max_ready_entry = max(ready_entries)
            if max_ready_entry > self.commit_length and self.log[max_ready_entry - 1].term == self.current_term:
                for i in range(self.commit_length, max_ready_entry):
                    entry = self.log[i]
                    if entry.operation == "SET":
                        self.data_store[entry.key] = entry.value
                        self.write_to_dump_file(f"Node {self.node_id} (leader) committed the entry {entry.operation} {entry.key} {entry.value} to the state machine.")
                self.commit_length = max_ready_entry
                self.store_state()

    # Update Current Term, Log Up To Date, Grant Vote, Deny Vote functions for Request Vote RPC
    def update_current_term_if_needed(self, vote_request):
        """Update the current term if the vote request term is greater than the current term"""
        if vote_request.term > self.current_term:
            self.current_term = vote_request.term
            self.voted_for = None
            self.store_state()
            self.step_down()

    def is_log_up_to_date(self, vote_request):
        """Check if the log is up to date with the vote request log"""
        last_log_term = self.log[-1].term if self.log else 0
        log_is_up_to_date = (vote_request.last_log_term > last_log_term) or \
                            (vote_request.last_log_term == last_log_term and vote_request.last_log_index >= len(self.log))
        return log_is_up_to_date

    def grant_vote_to_candidate(self, vote_request):
        """Grant vote to the candidate if the log is up to date and the candidate has not voted for another candidate"""
        self.voted_for = vote_request.candidate_id
        self.store_state()
        self.write_to_dump_file(f"Vote granted for Node {vote_request.candidate_id} in term {vote_request.term}.")
        remaining_lease_duration = max(0, self.old_leader_lease_timeout - (time.time() - self.lease_start_time))
        return raft_pb2.RequestVoteReply(
            term=self.current_term,
            vote_granted=True,
            old_leader_lease_timeout=remaining_lease_duration
        )

    def deny_vote_to_candidate(self, vote_request):
        """Deny vote to the candidate if the log is not up to date or the candidate has voted for another candidate"""
        self.write_to_dump_file(f"Vote denied for Node {vote_request.candidate_id} in term {vote_request.term}.")
        return raft_pb2.RequestVoteReply(
            term=self.current_term,
            vote_granted=False,
            old_leader_lease_timeout=self.old_leader_lease_timeout
        )

    def RequestVote(self, vote_request, context):
        """Handle the RequestVote RPC from a candidate"""
        self.update_current_term_if_needed(vote_request)

        if vote_request.term != self.current_term or self.voted_for not in (None, vote_request.candidate_id):
            return self.deny_vote_to_candidate(vote_request)

        if self.is_log_up_to_date(vote_request):
            return self.grant_vote_to_candidate(vote_request)

        return self.deny_vote_to_candidate(vote_request)

    # Update Current Term, Follower State, Log Consistent, Append Entries to Log functions for Append Entries RPC
    def update_current_term_if_needed(self, append_entries_request):
        """Update the current term if the append entries request term is greater than the current term"""
        if append_entries_request.term > self.current_term:
            self.current_term = append_entries_request.term
            self.voted_for = None
            self.store_state()
            self.step_down()

    def update_follower_state(self, append_entries_request):
        """Update the follower state if the append entries request term is equal to the current term"""
        if append_entries_request.term == self.current_term:
            self.state = FOLLOWER
            self.current_leader = append_entries_request.leader_id
            self.cancel_election_timer()
            self.old_leader_lease_timeout = append_entries_request.lease_duration
            self.lease_start_time = time.time()
            self.start_election_timer()

    def is_log_consistent(self, append_entries_request):
        """Check if the log is consistent with the append entries request"""
        log_is_consistent = (len(self.log) >= append_entries_request.prev_log_index) and \
                            (append_entries_request.prev_log_index == 0 or self.log[append_entries_request.prev_log_index - 1].term == append_entries_request.prev_log_term)
        return log_is_consistent

    def append_entries_to_log(self, prev_log_index, leader_commit, entries):
        """Append entries to the log and commit the entries if the leader commit index is greater than the current commit index"""
        if entries and len(self.log) > prev_log_index:
            index = min(len(self.log), prev_log_index + len(entries)) - 1
            if self.log[index].term != entries[index - prev_log_index].term:
                self.log = self.log[:prev_log_index]
        if prev_log_index + len(entries) > len(self.log):
            self.log.extend(entries[len(self.log) - prev_log_index:])
        if leader_commit > self.commit_length:
            for i in range(self.commit_length, leader_commit):
                entry = self.log[i]
                if entry.operation == "SET":
                    self.data_store[entry.key] = entry.value
                    self.write_to_dump_file(f"Node {self.node_id} (follower) committed the entry {entry.operation} {entry.key} {entry.value} to the state machine.")
            self.commit_length = leader_commit
        self.store_state()

    def AppendEntries(self, append_entries_request, context):
        """Handle the AppendEntries RPC from the leader"""
        self.update_current_term_if_needed(append_entries_request)
        self.update_follower_state(append_entries_request)

        if append_entries_request.term == self.current_term and self.is_log_consistent(append_entries_request):
            self.append_entries_to_log(append_entries_request.prev_log_index, append_entries_request.leader_commit, append_entries_request.entries)
            ack = append_entries_request.prev_log_index + len(append_entries_request.entries)
            self.write_to_dump_file(f"Node {self.node_id} accepted AppendEntries RPC from {append_entries_request.leader_id}.")
            return raft_pb2.AppendEntriesReply(term=self.current_term, success=True, ack=ack)
        else:
            self.write_to_dump_file(f"Node {self.node_id} rejected AppendEntries RPC from {append_entries_request.leader_id}.")
            return raft_pb2.AppendEntriesReply(term=self.current_term, success=False, ack=0)

    # Handle Get and Set Request functions for the client requests
    def handle_get_request(self, key):
        """Handle the GET request from the client"""
        value = self.data_store.get(key, "")
        return raft_pb2.ServeClientReply(Data=value, LeaderID=str(self.node_id), Success=True)

    def handle_set_request(self, key, value):
        """Handle the SET request from the client"""
        log_entry = raft_pb2.LogEntry(operation="SET", key=key, value=value, term=self.current_term)
        self.log.append(log_entry)
        self.store_state()

        # Wait for the entry to be committed
        while self.commit_length < len(self.log):
            time.sleep(0.1)

        # Check if the committed entry matches the appended entry
        if self.log[self.commit_length - 1] == log_entry:
            return raft_pb2.ServeClientReply(Data="", LeaderID=str(self.node_id), Success=True)
        else:
            return raft_pb2.ServeClientReply(Data="", LeaderID=str(self.node_id), Success=False)

    def ServeClient(self, client_request, context):
        """Handle the client request based on the current node state"""
        if self.state == LEADER:
            request_parts = client_request.Request.split()
            operation = request_parts[0]

            if operation == "GET":
                key = request_parts[1]
                return self.handle_get_request(key)
            elif operation == "SET":
                key = request_parts[1]
                value = request_parts[2]
                return self.handle_set_request(key, value)
        else:
            return raft_pb2.ServeClientReply(Data="", LeaderID=str(self.current_leader), Success=False)

def clean_logs(node_id):
    """Clean logs, metadata, and dump text files for a node."""
    log_dir = f"logs_node_{node_id}"
    if os.path.exists(log_dir):
        for filename in os.listdir(log_dir):
            os.remove(os.path.join(log_dir, filename))
        print(f"Cleaned logs for node {node_id}")

def serve(node_id, node_addresses):
    """Start the Raft server for a node"""
    node = Raft(node_id, node_addresses)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raft_pb2_grpc.add_RaftServicer_to_server(node, server)
    # server.add_insecure_port("0.0.0.0" + node_addresses[node_id][node_addresses[node_id].find(':'):])
    server.add_insecure_port(node_addresses[node_id])
    server.start()
    print(f"Started {node_id} server at {node_addresses[node_id]}")
    node.start_election_timer()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop(0)

def main():
    """Main function to parse command line arguments and start the Raft server"""
    if len(sys.argv) < 4:
        print("Usage: python server.py <node_id> <clear data (optional)>")
        sys.exit(1)
    node_id = int(sys.argv[1])
    num_of_nodes = int(sys.argv[2])
    clear_data = sys.argv[3] if len(sys.argv) > 3 else "false"
    # node_addresses = {
    #     0: "localhost:50050",
    #     1: "localhost:50051",
    #     2: "localhost:50052",
    #     3: "localhost:50053",
    #     4: "localhost:50054",
    # }
    node_addresses={i:f"10.128.0.{i+2}:5005{i}" for i in range(num_of_nodes)}
    # node_addresses = {
        # 0: "34.41.170.86:50050",
        # 1: "35.202.160.202:50051",
        # 2: "35.222.95.185:50052",
        # 3: "35.226.206.149:50053",
        # 4: "35.238.193.92:50054",
        # }
    if clear_data.lower() == "true":
        clean_logs(node_id)

    serve(node_id, node_addresses)

if __name__ == "__main__":
    main()
import grpc
import raft_pb2
import raft_pb2_grpc
import random
import time
import threading
import os
import sys
from concurrent import futures

# Setting time constants and state constants
HEARTBEAT_INTERVAL_SECONDS = 1.0
ELECTION_TIMEOUT_MIN = 5.0
ELECTION_TIMEOUT_MAX = 10.0
LEASE_DURATION_SECONDS = 10
FOLLOWER_STATE = 0
CANDIDATE_STATE = 1
LEADER_STATE = 2

class Raft(raft_pb2_grpc.RaftServicer):
    def __init__(self, nodeID, nodeAddresses):
        self.nodeID = nodeID
        self.state = FOLLOWER_STATE
        self.currentTerm = 0
        self.nodeAddresses = nodeAddresses
        self.votedFor = None
        self.log = []
        self.DataStorage = {}
        self.commitLen = 0
        self.currentLeader = None
        self.receivedVotes = set()
        self.logLengthSent = {}
        self.logLengthAcknowledged = {}
        self.electionTimeout = None
        self.heartbeatCycle = None
        self.leasePeriod = None
        self.old_leader_lease_timeout = 0
        self.leaseStartTime = 0
        self.loadServerState()
        self.initLogDirectory()

    # Create and write functions to dump info
    def initLogDirectory(self):
        """Create the dump file for the node."""
        os.makedirs(f"logs_node_{self.nodeID}", exist_ok=True)
        try:
            self.dump_file = open(f"logs_node_{self.nodeID}/dump.txt", "a")
        except FileNotFoundError:
            self.dump_file = open(f"logs_node_{self.nodeID}/dump.txt", "w")

    def logMessage(self, message):
        """Write a message to the dump file with a timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.dump_file.write(log_message + "\n")
        self.dump_file.flush()

    # Store and Load state functions to persist the logs and metadata
    def loadServerState(self):
        """Load the state from disk to recover the logs and metadata"""
        log_file_path = f"logs_node_{self.nodeID}/logs.txt"
        metadata_file_path = f"logs_node_{self.nodeID}/metadata.txt"

        try:
            with open(metadata_file_path, "r") as metadata_file:
                self.commitLen = int(metadata_file.readline().strip())
                self.currentTerm = int(metadata_file.readline().strip())
                self.votedFor = metadata_file.readline().strip() or None

            with open(log_file_path, "r") as log_file:
                for line in log_file:
                    parts = line.strip().split(" ")
                    if parts[0] == "NO-OP":
                        term = int(parts[1])
                        self.log.append(raft_pb2.LogEntry(operation="NO-OP", term=term))
                    elif parts[0] == "SET":
                        key, value, term = parts[1], parts[2], int(parts[3])
                        self.log.append(raft_pb2.LogEntry(operation="SET", key=key, value=value, term=term))
                        if len(self.log) <= self.commitLen:
                            self.DataStorage[key] = value
        except FileNotFoundError:
            pass

    def store_state(self):
        """Save the current state on disk to persist the logs and metadata"""
        log_file_path = f"logs_node_{self.nodeID}/logs.txt"
        metadata_file_path = f"logs_node_{self.nodeID}/metadata.txt"

        os.makedirs(f"logs_node_{self.nodeID}", exist_ok=True)

        with open(log_file_path, "w") as log_file:
            for entry in self.log:
                if entry.operation == "NO-OP":
                    log_file.write(f"NO-OP {entry.term}\n")
                elif entry.operation == "SET":
                    log_file.write(f"SET {entry.key} {entry.value} {entry.term}\n")
                elif entry.operation == "GET":
                    log_file.write(f"GET {entry.key} {entry.value} {entry.term}\n")

        with open(metadata_file_path, "w") as metadata_file:
            metadata_file.write(f"{self.commitLen}\n")
            metadata_file.write(f"{self.currentTerm}\n")
            metadata_file.write(f"{self.votedFor or ''}\n")

    # Start Timer functions for election, heartbeat and lease
    # Threading.Timer is used to start a timer that will run a function after a specified number of seconds
    def _beginElectionCountdown(self):
        """Start the election timer with a random duration"""
        election_timeout = random.uniform(ELECTION_TIMEOUT_MIN, ELECTION_TIMEOUT_MAX)
        self.electionTimeout = threading.Timer(election_timeout, self._triggerElection)
        self.electionTimeout.start()

    def _initiateHeartbeatCycle(self):
        """Start the heartbeat timer with a fixed interval"""
        self.heartbeatCycle = threading.Timer(HEARTBEAT_INTERVAL_SECONDS, self._issueHeartbeats)
        self.heartbeatCycle.start()

    def _startLeaseCountdown(self):
        """Start the lease timer with a fixed duration"""
        self.leaseStartTime = time.time()
        self.leasePeriod = threading.Timer(LEASE_DURATION_SECONDS, self.lease_timeout)
        self.leasePeriod.start()

    # Cancel Timer functions for election, heartbeat and lease
    def _stopElectionTimer(self):
        """Cancel the election timer if it is active"""
        if self.electionTimeout:
            self.electionTimeout.cancel()

    def _haltHeartbeatTimer(self):
        """Cancel the heartbeat timer if it is active"""
        if self.heartbeatCycle:
            self.heartbeatCycle.cancel()

    def _terminateLeaseTimer(self):
        """Cancel the lease timer if it is active"""
        if self.leasePeriod:
            self.leasePeriod.cancel()

    # Start and Check Election functions for the election process
    def _evaluateElectionOutcome(self):
        """Check the result of the election after the election timer expires"""
        if len(self.receivedVotes) < (len(self.nodeAddresses) // 2) + 1:
            self._beginElectionCountdown()
        else:
            self._ascendToLeader()

    def _triggerElection(self):
        """Start the election process by incrementing the term and requesting votes from other nodes"""
        self.logMessage(f"Node {self.nodeID} election timeout. Starting new election.")
        self.state = CANDIDATE_STATE
        self.currentTerm += 1
        self.votedFor = self.nodeID
        self.receivedVotes = {self.nodeID}

        last_term = 0
        if self.log:
            last_term = self.log[-1].term
        self.store_state()

        threads = []
        for nodeID, _ in self.nodeAddresses.items():
            if nodeID == self.nodeID:
                continue
            else:
                thread = self._requestVoteAsync(nodeID, last_term)
                threads.append(thread)

        timer = threading.Timer(0.1, self._evaluateElectionOutcome)
        timer.start()
       
    # Create, Send and Request Vote functions for the election process   
    def _generateVoteRequest(self, nodeID, last_term):
        """Create a vote request for a specific node"""
        channel = grpc.insecure_channel(self.nodeAddresses[nodeID])
        stub = raft_pb2_grpc.RaftStub(channel)

        request = raft_pb2.RequestVoteArgs(
            term=self.currentTerm,
            candidate_id=self.nodeID,
            last_log_index=len(self.log),
            last_log_term=last_term
        )
        return stub, request, channel

    def _dispatchVoteRequest(self, stub, request, nodeID, channel):
        """Send a vote request to a specific node"""
        try:
            response = stub.RequestVote(request, timeout=1)

            if response.vote_granted:
                self.receivedVotes.add(nodeID)

                remaining_lease_duration = self.old_leader_lease_timeout - (time.time() - self.leaseStartTime)
                if remaining_lease_duration < 0:
                    remaining_lease_duration = 0
                self.old_leader_lease_timeout = max(remaining_lease_duration, response.old_leader_lease_timeout)
                    
        except grpc.RpcError as e:
            # Handle any errors that occur during the RPC
            self.logMessage(f"Error occurred while sending RPC to Node {nodeID}.")
        finally:
            channel.close()

    def _requestVoteAsync(self, nodeID, last_term):
        """Start the request_vote_task in a separate thread and return the thread object"""
        stub, request, channel = self._generateVoteRequest(nodeID, last_term)
        thread = threading.Thread(target=self._dispatchVoteRequest, args=(stub, request, nodeID, channel))
        thread.start()
        return thread

    # Become Leader function to handle the leader election process
    def _ascendToLeader(self):
        """Handle the leader election process after receiving votes from a majority of nodes"""
        self.logMessage(f"Node {self.nodeID} is the leader for term {self.currentTerm}.")
        self.state = LEADER_STATE
        self.currentLeader = self.nodeID
        self.receivedVotes = set()
        self.logLengthSent = {nodeID: len(self.log) for nodeID in self.nodeAddresses}
        self.logLengthAcknowledged = {nodeID: 0 for nodeID in self.nodeAddresses}
        self._stopElectionTimer()

        self.logMessage("Waiting for Old Leader Lease to timeout.")
        time.sleep(self.old_leader_lease_timeout)

        self._startLeaseCountdown()
        self._logNoOpEntry()
        self._issueHeartbeats()

    def lease_timeout(self):
        """Handle the case when the leader lease expires without renewing the lease"""
        self.logMessage(f"Leader {self.nodeID} lease renewal failed. Stepping Down.")
        self._revertToFollower()

    def _revertToFollower(self):
        """Step down from the leader role and become a follower"""
        self.logMessage(f"{self.nodeID} Stepping down")
        self.state = FOLLOWER_STATE
        self.currentLeader = None
        self.receivedVotes = set()
        self.logLengthSent = {}
        self.logLengthAcknowledged = {}
        self._haltHeartbeatTimer()
        self._terminateLeaseTimer()
        self._stopElectionTimer()
        self._beginElectionCountdown()

    def _logNoOpEntry(self):
        """Append a NO-OP entry to the log to maintain the leader lease"""
        self.log.append(raft_pb2.LogEntry(operation="NO-OP", term=self.currentTerm))
        self.store_state()

    # Create, Send and Heartbeat functions for the leader to send heartbeats to followers
    def _generateHeartbeatSignal(self):
        """Create a heartbeat for all the followers"""
        threads = []
        self.heartbeat_success_nodes = set()
        for nodeID, node_address in self.nodeAddresses.items():
            if nodeID != self.nodeID:
                thread = self.ReplicateLogAsync(nodeID)
                threads.append(thread)
        return threads

    def _broadcastHeartbeat(self):
        """Send the heartbeat to all the followers and check the lease renewal"""
        def check_lease_renewal():
            if len(self.heartbeat_success_nodes) < (len(self.nodeAddresses) // 2):
                self.logMessage(f"Leader {self.nodeID} failed to renew lease. Stepping down.")
                self._revertToFollower()

        remaining_lease_time = self.leasePeriod.interval - (time.time() - self.leaseStartTime)
        timer = threading.Timer(remaining_lease_time, check_lease_renewal)
        timer.start()
        self._initiateHeartbeatCycle()

    def _issueHeartbeats(self):
        """Using the _generateHeartbeatSignal and _broadcastHeartbeat functions"""
        self.logMessage(f"Leader {self.nodeID} sending heartbeat & Renewing Lease")
        self.leasePeriod.cancel()
        self._startLeaseCountdown()
        self._generateHeartbeatSignal()
        self._broadcastHeartbeat()
        
    # Create, Send and Replicate Log functions for the leader to replicate logs to followers    
    def CreateLogReplication(self, follower_id):
        """Create a log replication for a specific follower"""
        channel = grpc.insecure_channel(self.nodeAddresses[follower_id])
        stub = raft_pb2_grpc.RaftStub(channel)
        prefix_length = self.logLengthSent.get(follower_id, 0)
        suffix = self.log[prefix_length:]
        prefix_term = 0
        if prefix_length > 0:
            prefix_term = self.log[prefix_length - 1].term
        request = raft_pb2.AppendEntriesArgs(
            term=self.currentTerm,
            leader_id=self.nodeID,
            prev_log_index=prefix_length,
            prev_log_term=prefix_term,
            entries=suffix,
            leader_commit=self.commitLen,
            lease_duration=LEASE_DURATION_SECONDS
        )
        return stub, request, prefix_length, suffix, channel

    def SendLogReplication(self, stub, request, follower_id, prefix_length, suffix, channel):
        """Send a log replication to a specific follower"""
        try:
            response = stub.AppendEntries(request, timeout=1)
            if response.success:
                self.logLengthSent[follower_id] = prefix_length + len(suffix)
                self.logLengthAcknowledged[follower_id] = prefix_length + len(suffix)
                self.CommitLogEntries()
                self.heartbeat_success_nodes.add(follower_id)
            else:
                self.logLengthSent[follower_id] = max(0, self.logLengthSent.get(follower_id, 0) - 1)
                self.ReplicateLogAsync(follower_id)
        except grpc.RpcError as e:
            self.logMessage(f"Error occurred while sending RPC to Node {follower_id}.")
        finally:
            channel.close()

    def ReplicateLogAsync(self, follower_id):
        """Start the replicate_log_task in a separate thread and return the thread object"""
        stub, request, prefix_length, suffix, channel = self.CreateLogReplication(follower_id)
        thread = threading.Thread(target=self.SendLogReplication, args=(stub, request, follower_id, prefix_length, suffix, channel))
        thread.start()
        return thread
    
    # Commit Log Entries function to commit the log entries
    def CommitLogEntries(self):
        """Commit log entries if a majority of nodes have replicated them"""
        min_acks = len(self.nodeAddresses) // 2
        ready_entries = [index for index in range(1, len(self.log) + 1) if len([nodeID for nodeID, logLengthAcknowledged in self.logLengthAcknowledged.items() if logLengthAcknowledged >= index]) >= min_acks]

        if ready_entries:
            max_ready_entry = max(ready_entries)
            if max_ready_entry > self.commitLen and self.log[max_ready_entry - 1].term == self.currentTerm:
                for i in range(self.commitLen, max_ready_entry):
                    entry = self.log[i]
                    if entry.operation == "SET":
                        self.DataStorage[entry.key] = entry.value
                        self.logMessage(f"Node {self.nodeID} (leader) committed the entry {entry.operation} {entry.key} {entry.value} to the state machine.")
                self.commitLen = max_ready_entry
                self.store_state()

    # Update Current Term, Log Up To Date, Grant Vote, Deny Vote functions for Request Vote RPC
    def UpdateCurrentTermIfNeeded(self, vote_request):
        """Update the current term if the vote request term is greater than the current term"""
        if vote_request.term > self.currentTerm:
            self.currentTerm = vote_request.term
            self.votedFor = None
            self.store_state()
            self._revertToFollower()

    def LogUptoDate(self, vote_request):
        """Check if the log is up to date with the vote request log"""
        last_log_term = self.log[-1].term if self.log else 0
        log_is_up_to_date = (vote_request.last_log_term > last_log_term) or (vote_request.last_log_term == last_log_term and vote_request.last_log_index >= len(self.log))
        return log_is_up_to_date

    def grant_vote_to_candidate(self, vote_request):
        """Grant vote to the candidate if the log is up to date and the candidate has not voted for another candidate"""
        self.votedFor = vote_request.candidate_id
        self.store_state()
        self.logMessage(f"Vote granted for Node {vote_request.candidate_id} in term {vote_request.term}.")
        remaining_lease_duration = max(0, self.old_leader_lease_timeout - (time.time() - self.leaseStartTime))
        return raft_pb2.RequestVoteReply(
            term=self.currentTerm,
            vote_granted=True,
            old_leader_lease_timeout=remaining_lease_duration
        )

    def DenyVoteCandidate(self, vote_request):
        """Deny vote to the candidate if the log is not up to date or the candidate has voted for another candidate"""
        self.logMessage(f"Vote denied for Node {vote_request.candidate_id} in term {vote_request.term}.")
        return raft_pb2.RequestVoteReply(
            term=self.currentTerm,
            vote_granted=False,
            old_leader_lease_timeout=self.old_leader_lease_timeout
        )

    def RequestVote(self, vote_request, context):
        """Handle the RequestVote RPC from a candidate"""
        self.UpdateCurrentTermIfNeeded(vote_request)

        if vote_request.term != self.currentTerm or self.votedFor not in (None, vote_request.candidate_id):
            return self.DenyVoteCandidate(vote_request)

        if self.LogUptoDate(vote_request):
            return self.grant_vote_to_candidate(vote_request)

        return self.DenyVoteCandidate(vote_request)

    # Update Current Term, Follower State, Log Consistent, Append Entries to Log functions for Append Entries RPC
    def UpdateCurrentTermIfNeeded(self, append_entries_request):
        """Update the current term if the append entries request term is greater than the current term"""
        if append_entries_request.term > self.currentTerm:
            self.currentTerm = append_entries_request.term
            self.votedFor = None
            self.store_state()
            self._revertToFollower()

    def UpdateFollwerState(self, append_entries_request):
        """Update the follower state if the append entries request term is equal to the current term"""
        if append_entries_request.term == self.currentTerm:
            self.state = FOLLOWER_STATE
            self.currentLeader = append_entries_request.leader_id
            self._stopElectionTimer()
            self.old_leader_lease_timeout = append_entries_request.lease_duration
            self.leaseStartTime = time.time()
            self._beginElectionCountdown()

    def CheckLogConsistency(self, append_entries_request):
        """Check if the log is consistent with the append entries request"""
        log_is_consistent = (len(self.log) >= append_entries_request.prev_log_index) and (append_entries_request.prev_log_index == 0 or self.log[append_entries_request.prev_log_index - 1].term == append_entries_request.prev_log_term)
        return log_is_consistent

    def AppendEntriesForLog(self, prev_log_index, leader_commit, entries):
        """Append entries to the log and commit the entries if the leader commit index is greater than the current commit index"""
        if entries and len(self.log) > prev_log_index:
            index = min(len(self.log), prev_log_index + len(entries)) - 1
            if self.log[index].term != entries[index - prev_log_index].term:
                self.log = self.log[:prev_log_index]
        if prev_log_index + len(entries) > len(self.log):
            self.log.extend(entries[len(self.log) - prev_log_index:])
        if leader_commit > self.commitLen:
            for i in range(self.commitLen, leader_commit):
                entry = self.log[i]
                if entry.operation == "SET":
                    self.DataStorage[entry.key] = entry.value
                    self.logMessage(f"Node {self.nodeID} (follower) committed the entry {entry.operation} {entry.key} {entry.value} to the state machine.")
            self.commitLen = leader_commit
        self.store_state()

    def AppendEntries(self, append_entries_request, context):
        """Handle the AppendEntries RPC from the leader"""
        self.UpdateCurrentTermIfNeeded(append_entries_request)
        self.UpdateFollwerState(append_entries_request)

        if append_entries_request.term == self.currentTerm and self.CheckLogConsistency(append_entries_request):
            self.AppendEntriesForLog(append_entries_request.prev_log_index, append_entries_request.leader_commit, append_entries_request.entries)
            ack = append_entries_request.prev_log_index + len(append_entries_request.entries)
            self.logMessage(f"Node {self.nodeID} accepted AppendEntries RPC from {append_entries_request.leader_id}.")
            return raft_pb2.AppendEntriesReply(term=self.currentTerm, success=True, ack=ack)
        else:
            self.logMessage(f"Node {self.nodeID} rejected AppendEntries RPC from {append_entries_request.leader_id}.")
            return raft_pb2.AppendEntriesReply(term=self.currentTerm, success=False, ack=0)

    # Handle Get and Set Request functions for the client requests
    def handle_get_request(self, key):
        """Handle the GET request from the client"""
        value = self.DataStorage.get(key, "")
        self.logMessage(f"Node {self.nodeID} received GET request for key {key}. Returned value: {value}")
        log_entry = raft_pb2.LogEntry(operation="GET", key=key, value=value, term=self.currentTerm)
        self.log.append(log_entry)
        self.store_state()
        return raft_pb2.ServeClientReply(Data=value, LeaderID=str(self.nodeID), Success=True)
    
    def handle_set_request(self, key, value):
        """Handle the SET request from the client"""
        log_entry = raft_pb2.LogEntry(operation="SET", key=key, value=value, term=self.currentTerm)
        self.log.append(log_entry)
        self.store_state()

        # Wait for the entry to be committed
        while self.commitLen < len(self.log):
            time.sleep(0.1)

        # Check if the committed entry matches the appended entry
        if self.log[self.commitLen - 1] == log_entry:
            return raft_pb2.ServeClientReply(Data="", LeaderID=str(self.nodeID), Success=True)
        else:
            return raft_pb2.ServeClientReply(Data="", LeaderID=str(self.nodeID), Success=False)

    def ServeClient(self, client_request, context):
        """Handle the client request based on the current node state"""
        if self.state == LEADER_STATE:
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
            return raft_pb2.ServeClientReply(Data="", LeaderID=str(self.currentLeader), Success=False)

def clearNodeLogs(nodeID):
    """Clean logs, metadata, and dump text files for a node."""
    log_dir = f"logs_node_{nodeID}"
    if os.path.exists(log_dir):
        for filename in os.listdir(log_dir):
            os.remove(os.path.join(log_dir, filename))
        print(f"Cleaned logs for node {nodeID}")

def launchNodeServer(nodeID, nodeAddresses):
    """Start the Raft server for a node"""
    node = Raft(nodeID, nodeAddresses)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raft_pb2_grpc.add_RaftServicer_to_server(node, server)
    # server.add_insecure_port("0.0.0.0" + nodeAddresses[nodeID][nodeAddresses[nodeID].find(':'):])
    server.add_insecure_port(nodeAddresses[nodeID])
    server.start()
    print(f"Started {nodeID} server at {nodeAddresses[nodeID]}")
    node._beginElectionCountdown()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop(0)

def main():
    """Main function to parse command line arguments and start the Raft server"""
    if len(sys.argv) < 2:
        print("Usage: python server.py <nodeID> <clear data (optional)>")
        sys.exit(1)
    nodeID = int(sys.argv[1])
    clear_data = sys.argv[2] if len(sys.argv) > 2 else "false"
    nodeAddresses = {
        0: "localhost:50050",
        1: "localhost:50051",
        2: "localhost:50052",
        3: "localhost:50053",
        4: "localhost:50054",
    }
    # nodeAddresses = {
    #     0: "10.128.0.2:50050",
    #     1: "10.128.0.3:50051",
    #     2: "10.128.0.4:50052",
    #     3: "10.128.0.5:50053",
    #     4: "10.128.0.6:50054",
    # }
    if clear_data.lower() == "true":
        clearNodeLogs(nodeID)

    launchNodeServer(nodeID, nodeAddresses)

if __name__ == "__main__":
    main()
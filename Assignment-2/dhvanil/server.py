import sys
import os
import time
from threading import Thread, Timer, Lock, Condition
from concurrent import futures

import random
import grpc
import raft_pb2 as pb2
import raft_pb2_grpc as pb2_grpc

ID = int(sys.argv[1])
SERVERS_INFO = {}
LEASE_DURATION = 2.5
HEARTBEAT_INTERVAL = 1

class Server:
    def __init__(self, log_number):
        self.vote_lock = Lock()
        self.state = "Follower" # Initial state
        self.term = 0 # Current term starts at 0
        self.id = ID # Server ID

        self.votedFor = None  # Tracks who the server voted for
        self.leaderId = None # ID of the current leader, if known
        self.timeout = None # Election timeout
        self.sleep = False # Flag to indicate if the server is sleeping
        self.timer = None # Timer for election timeout
        self.threads = [] # List of threads for election
        
        self.database = {} # Key-value store
        self.log = [] # Log of commands
        self.leaseExpiration = 0 # Time when the lease expires
        self.votesReceived = 0  # Votes received in the current election
        self.nextIndex = {} # For each server, index of the next log entry to send to that server
        self.matchIndex = {} # For each server, index of the highest log entry known to be replicated on server
        self.commitIndex = 0 # Index of highest log entry known to be committed
        self.lastApplied = 0 # Index of highest log entry applied to state machine
        
        self.log_file = open(f"logs_node_{log_number}\logs.txt", "a+") # Log file to store information about the server
        self.dump_file = open(f"logs_node_{log_number}\dump.txt", "a+") # Dump file to store print statements
        self.metadata_file = open(f"logs_node_{log_number}\metadata.txt", "a+") # Metadata file to store metadata about the server
        self.commitCondition = Condition()  # Condition variable for log commits

        self.load_persisted_data(log_number)
        self.start()

    def start(self):
        """Initialize server state and start the election timeout timer."""
        self.set_timeout()
        self.timer = Timer(0, self.become_follower)
        self.timer.start()

    def set_timeout(self):
        """Set a random timeout for election."""
        if self.sleep:
            return
        self.timeout = random.uniform(5, 10)

    def reset_timer(self, timeout, func):
        """Reset the election timeout timer."""
        self.timer.cancel()
        self.timer = Timer(timeout, func)
        self.timer.start()

    def update_state(self, state):
        """Update the server state."""
        if self.sleep:
            return
        self.state = state
        print(f"Server {self.id} is now a {self.state}", file=self.dump_file)

    def update_term(self, term):
        """Update the server term."""
        if self.sleep:
            return
        self.term = term
        self.votedFor = None
        print(f"Server {self.id} term is now {self.term}", file=self.dump_file)
        self.log_file.write(f"Term: {self.term}, VotedFor: {self.votedFor}\n")
        self.log_file.flush()
        self.metadata_file.write(f"{self.term},{self.votedFor},{self.commitIndex}\n")
        self.metadata_file.flush()

    # For all 3 follower states (Follower, Candidate, Leader)
    # For Follower 
    def become_follower(self):
        """Become a follower."""
        self.update_state("Follower")
        self.reset_timer(self.timeout, self.follower_activity)

    def follower_activity(self):
        """ If it doesn't receive any communication from the leader, start election."""
        if self.sleep or self.state != "Follower":
            return
        
        print(f"Server {self.id} timed out")
        print(f"Term: {self.term}, has not heard from leader {self.leaderId}")
        self.leaderId = None
        self.become_candidate()

    # For Candidate
    def become_candidate(self):
        """Become a candidate."""
        if self.sleep:
            return
        
        self.update_state("Candidate")
        self.update_term(self.term + 1)
        self.votedFor = self.id
        self.votesReceived = 1

        print(f"Server {self.id} is now a candidate for term {self.term}")
        
        self.reset_timer(self.timeout, self.candidate_activity)
        self.candidate_election()

    def candidate_election(self):
        """Initiate a new candidate election by requesting votes from all other servers."""
        self.votesReceived = 1  # Vote for self
        self.threads = []
        
        for server_id, server_info in SERVERS_INFO.items():
            if server_id != self.id:
                thread = Thread(target=self.request_vote, args=(server_id, server_info))
                self.threads.append(thread)
                thread.start()

        for thread in self.threads:
            thread.join()

        print("temp working 0")
        # Move majority check here to ensure it's done immediately after votes are collected
        with self.vote_lock:
            if self.votesReceived > len(SERVERS_INFO) // 2 and self.state == "Candidate":
                print("temp working 1")
                self.become_leader()
            else:
                print("temp working 2")
                self.set_timeout()
                self.become_follower()


    def candidate_activity(self):
        """Action taken by the candidate after election timeout."""
        if self.sleep or self.state != "Candidate":
            return
        
        for thread in self.threads:
            thread.join(1)

        print(f"Server {self.id} received {self.votesReceived} votes for term {self.term}")

        with self.vote_lock:
            if self.votesReceived <= len(SERVERS_INFO) // 2:
                self.set_timeout()
                self.become_follower()
            else:
                self.timeout = 0.5
                self.become_leader()

    # For Leader
    def become_leader(self):
        """Become a leader."""
        if self.sleep:
            return
        
        self.update_state("Leader")
        self.leaderId = self.id

        self.nextIndex = {server_id: (len(self.log)+1) for server_id in SERVERS_INFO}
        self.matchIndex = {server_id: 0 for server_id in SERVERS_INFO}

        print("temp working 3")
        print(f"Server {self.id} is now a leader for term {self.term}", file=self.dump_file)

        self.leader_activity()

    def leader_activity(self):
        """Leader sends heartbeats to all followers to maintain its state and lease."""
        if self.sleep or self.state != "Leader":
            return
        
        print(f"Leader {self.id} sending heartbeat & Renewing Lease", file=self.dump_file)
        self.update_lease(LEASE_DURATION)  # Update leader's lease expiration based on the current time
        
        self.threads = []
        for server_id, server_info in SERVERS_INFO.items():
            if server_id == self.id:
                continue
            self.threads.append(Thread(target=self.heartbeat, args=(server_id, server_info)))

        for thread in self.threads:
            thread.start()
        
        self.reset_timer(HEARTBEAT_INTERVAL, self.leader_check)
        
    def leader_check(self):
        """ Checks the database for commits and updates accordingly. """
        if self.sleep or self.state != "Leader":
            return
        
        for thread in self.threads:
            thread.join(1)

        self.nextIndex[self.id] = len(self.log) + 1
        self.matchIndex[self.id] = len(self.log)

        commits = sum(1 for server_id in SERVERS_INFO if self.matchIndex[server_id] > self.commitIndex and self.log[self.matchIndex[server_id] - 1]["term"] == self.term)

        if commits > len(self.matchIndex) // 2:
            self.commitIndex += 1
            with self.commitCondition:
                self.commitCondition.notify_all()  # Notify all waiting threads when a log entry is committed
        while self.commitIndex > self.lastApplied:
            key, value = self.log[self.lastApplied]["update"]["key"], self.log[self.lastApplied]["update"]["value"]
            self.database[key] = value
            print(f"Term : {self.term} and Key : {key} and Value : {value}")
            self.lastApplied += 1

        self.leader_activity()

        # Check if lease is still valid and schedule the next heartbeat
        if self.get_lease_duration() > 0:
            self.reset_timer(HEARTBEAT_INTERVAL, self.leader_activity)
        else:
            # Handle lease expiration (e.g., step down as leader)
            print(f"Leader {self.id}'s lease expired. Stepping down.")
            self.become_follower()

        # with self.commitCondition:
            # self.commitCondition.notify_all()

    def request_vote(self, server_id, server_info):
        """Send a RequestVote RPC to a server."""
        print(f"Server {self.id} is requesting vote from server {server_id}", file=self.dump_file)
    
        if self.sleep or self.state != "Candidate":
            return
    
        channel = grpc.insecure_channel(server_info)
        stub = pb2_grpc.RaftServiceStub(channel)
        message = pb2.RequestVoteMessage(
            term=int(self.term),
            candidateId=int(self.id),
            lastLogIndex=int(len(self.log)),
            lastLogTerm=int(self.log[-1]["term"] if self.log else 0),
            oldLeaderLeaseDuration=LEASE_DURATION
        )

        try:
            response = stub.RequestVote(message)
            reciever_term = response.term
            vote_granted = response.voteGranted
            old_lease = response.oldLeaderLeaseDuration
            if reciever_term > self.term:
                self.update_term(reciever_term)
                self.set_timeout()
                self.become_follower()
            elif vote_granted:
                with self.vote_lock:
                    self.votesReceived += 1
                    print(f"Server {self.id} received vote from server {server_id}")
                    self.log_file.write(f"Server {self.id} received vote from server {server_id}\n")
                    self.log_file.flush()

        except grpc.RpcError as e:
            print(f"Failed to request vote from server {server_id} due to {e}", file=self.dump_file)
            time.sleep(5)
            self.request_vote(server_id, server_info)

    def heartbeat(self, server_id, server_info):
        """Send a heartbeat to a server."""
        if self.sleep or self.state != "Leader":
            return
        
        channel = grpc.insecure_channel(server_info)
        stub = pb2_grpc.RaftServiceStub(channel)

        entries = []
        if self.nextIndex[server_id] <= len(self.log):
            log_entry = self.log[self.nextIndex[server_id]-1]
            if "key" in log_entry:
                entries = [pb2.LogEntry(
                    term=log_entry["term"],
                    key=log_entry["key"],
                    value=log_entry["value"],
                    command=log_entry["command"]
                )]

        prev_log_term = 0
        if self.nextIndex[server_id] > 1:
            prev_log_term = self.log[self.nextIndex[server_id]-2]["term"]

        message = pb2.AppendEntriesMessage(
            term=self.term,
            leaderId=self.id,
            prevLogIndex=self.nextIndex[server_id]-1,
            prevLogTerm=prev_log_term,
            entries=entries,
            leaderCommit=self.commitIndex,
            oldLeaderLeaseDuration=self.get_lease_duration()
        )

        try:
            response = stub.AppendEntries(message)
            reciever_term = response.term
            success = response.success
            if reciever_term > self.term:
                self.update_term(reciever_term)
                self.set_timeout()
                self.become_follower()
            
            elif success and len(entries) != 0:
                self.nextIndex[server_id] += 1
                self.matchIndex[server_id] = self.nextIndex[server_id] - 1
                self.log_file.write(f"Server {self.id} sent heartbeat to server {server_id}\n")
                self.log_file.flush()

            elif not success:
                self.nextIndex[server_id] -= 1
                self.matchIndex[server_id] = min(self.nextIndex[server_id] - 1, self.matchIndex[server_id])

        except grpc.RpcError as e:
            print(f"Failed to send heartbeat to server {server_id} due to {e}", file=self.dump_file)

    def get_lease_duration(self):
        """Calculates the remaining lease duration."""
        return max(0, self.leaseExpiration - time.time())

    def update_lease(self, oldLeaderLeaseDuration):
        """Updates the lease expiration time."""
        self.leaseExpiration = time.time() + oldLeaderLeaseDuration

    def load_persisted_data(self, node_id):
        log_path = f"Assignment-2/dhvanil/logs_node_{node_id}/logs.txt"
        metadata_path = f"Assignment-2/dhvanil/logs_node_{node_id}/metadata.txt"
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        # Load logs
        if os.path.exists(log_path):
            with open(log_path, "r") as file:
                for line in file:
                    term, command, key, value = line.strip().split(',')
                    self.log.append({"term": int(term), "command": command, "key": key, "value": value})
        
        # Load metadata
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as file:
                last_line = list(file)[-1]
                term, votedFor, commitIndex = last_line.strip().split(',')
                self.term = int(term)
                self.votedFor = int(votedFor) if votedFor.isdigit() else None
                self.commitIndex = int(commitIndex)

class Handler(pb2_grpc.RaftServiceServicer):
    def __init__(self, server):
        self.server = server
        
    def RequestVote(self, request, context):
        """Handle a RequestVote RPC."""
        if self.server.sleep:
            context.set_details("Server is sleeping")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            return pb2.VoteResponseMessage()
        
        reply = {"term": -1, "voteGranted": False, "oldLeaderLeaseDuration": self.server.get_lease_duration()}

        if request.term == self.server.term:
            if self.server.votedFor or request.lastLogIndex < len(self.server.log) or self.server.state != "Follower":
                reply = {"term": self.server.term, "voteGranted": False, "oldLeaderLeaseDuration": self.server.get_lease_duration()}
            elif request.lastLogIndex == len(self.server.log) and self.server.log[request.lastLogIndex - 1]["term"] != request.lastLogTerm:
                reply = {"term": self.server.term, "voteGranted": False, "oldLeaderLeaseDuration": self.server.get_lease_duration()}
            else:
                self.server.votedFor = True
                self.server.leaderId = request.candidateId
                print(f"Term : {self.server.term} and Voted for : {request.candidateId}")
                reply = {"term": self.server.term, "voteGranted": True, "oldLeaderLeaseDuration": self.server.get_lease_duration()}

            if self.server.state == "Follower":
                self.server.reset_timer(self.server.timeout, self.server.follower_activity)

        elif request.term > self.server.term:
            self.server.update_term(request.term)
            print(f"Term : {self.server.term} and Voted for : {request.candidateId}")
            self.server.leaderId = request.candidateId
            self.server.votedFor = True
            self.server.become_follower()
            reply = {"term": self.server.term, "voteGranted": True, "oldLeaderLeaseDuration": self.server.get_lease_duration()}

        else:
            reply = {"term": self.server.term, "voteGranted": False, "oldLeaderLeaseDuration": self.server.get_lease_duration()}
            if self.server.state == "Follower":
                self.reset_timer(self.server.timeout, self.server.follower_activity)

        return pb2.VoteResponseMessage(term=reply["term"], voteGranted=reply["voteGranted"], oldLeaderLeaseDuration=reply["oldLeaderLeaseDuration"])

    def AppendEntries(self, request, context):
        """Handle an AppendEntries RPC."""
        if self.server.sleep:
            context.set_details("Server is sleeping")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            return pb2.AppendEntriesResponseMessage()
        
        reply = {"term": -1, "success": False}

        if request.term >= self.server.term:
            if request.term > self.server.term:
                self.server.update_term(request.term)
                self.server.become_follower()
                self.server.leaderId = request.leaderId
            
            if len(self.server.log) < request.prevLogIndex :
                reply = {"term": self.server.term, "success": False}
                if self.server.state == "Follower":
                    self.server.reset_timer(self.server.timeout, self.server.follower_activity)

            else:
                if len(self.server.log) > request.prevLogIndex and self.server.log[request.prevLogIndex - 1]["term"] != request.prevLogTerm:
                    reply = {"term": self.server.term, "success": False}
                else:
                    if len(request.entries) != 0:
                        self.server.log.append({"term" : request.entries[0].term, "update" : {"command" : request.entries[0].update.command, "key" : request.entries[0].update.key, "value" : request.entries[0].update.value}})
                        self.server.log_file.write(f"{request.entries[0].term},{request.entries[0].update.command},{request.entries[0].update.key},{request.entries[0].update.value}\n")
                        self.server.log_file.flush()

                    if request.leaderCommit > self.server.commitIndex:
                        self.server.commitIndex = min(request.leaderCommit, len(self.server.log))
                        while self.server.commitIndex > self.server.lastApplied:
                            key, value = self.server.log[self.server.lastApplied]["update"]["key"], self.server.log[self.server.lastApplied]["update"]["value"]
                            self.server.database[key] = value
                            print(f"Term : {self.server.term} and Key : {key} and Value : {value}")
                            self.server.lastApplied += 1

                    reply = {"term": self.server.term, "success": True}
                    self.server.reset_timer(self.server.timeout, self.server.follower_activity)

        else:
            reply = {"term": self.server.term, "success": False}

        return pb2.AppendEntriesResponseMessage(term=reply["term"], success=reply["success"])
    
    def GetLeader(self, request, context):
        """ Method to handle a getLeader request """
        if self.server.sleep:
            context.set_details("Server is sleeping")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            return pb2.LeaderMessage()
        

        reply = {"leaderId": None , "leaderAddress": "empty"}

        if self.server.state == "Leader":
            print(f"Term : {self.server.term} , Leader : {self.server.leaderId}")
            reply = {"leaderId": self.server.leaderId, "leaderAddress": SERVERS_INFO[self.server.leaderId]}
            return pb2.LeaderMessage(leaderId=reply["leaderId"], leaderAddress=reply["leaderAddress"])
        
        else:
            return pb2.LeaderMessage(leaderId=reply["leaderId"], leaderAddress=reply["leaderAddress"])
        
    # def SetVal(self, request, context):
    #     if self.server.sleep:
    #         context.set_details("Server is sleeping")
    #         context.set_code(grpc.StatusCode.UNAVAILABLE)
    #         return pb2.OperationResponseMessage()
        
    #     reply = {"success": False}
    #     print(f"Recieved SetVal request for key {request.key} and value {request.value}")

    #     if self.server.state == "Leader":
    #         log_index = len(self.server.log)
    #         self.server.log.append({"term": self.server.term, "update": {"command": 'SET', "key": request.key, "value": request.value}})
    #         print(self.server.log)
            
    #         # # Wait until the log entry has been committed
    #         # while self.server.commitCondition:
    #         #     while self.server.commitIndex < log_index:
    #         #         self.server.commitCondition.wait()
            
    #         reply = {"success": True}
    #         print(f"Succesfully set value for key {request.key} and value {request.value}")
    #     # if self.server.state == "Leader":
    #     #     log_entry = {"term": self.server.term, "command": "SET", "key": request.key, "value": request.value}
    #     #     self.server.log.append(log_entry)
            
    #     #     log_index = len(self.server.log)
    #     #     self.server.log_file.write(f"{log_entry['term']},{log_entry['command']},{log_entry['key']},{log_entry['value']}\n")
    #     #     self.server.log_file.flush()
            
    #     #     # Wait for the entry to be committed
    #     #     with self.server.commitCondition:
    #     #         while self.server.lastApplied < log_index:
    #     #             self.server.commitCondition.wait()
            
    #     #     reply = {"success": True}

    #     elif self.server.state == "Follower":
    #         channel = grpc.insecure_channel(SERVERS_INFO[self.server.leaderId])
    #         stub = pb2_grpc.RaftServiceStub(channel)
    #         message = pb2.KeyValMessage(key = request.key, value = request.value)

    #         try:
    #             response = stub.SetVal(message)
    #             reply = {"success": response.success}
    #         except grpc.RpcError as e:
    #             print(f"Server is not able to send the message to leader {self.server.leaderId} due to {e}")

    #     return pb2.OperationResponseMessage(success=reply["success"])

    def SetVal(self, request, context):
        if self.server.sleep:
            context.set_details("Server is sleeping")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            return pb2.OperationResponseMessage()
        
        reply = {"success": False}
        print(f"Recieved SetVal request for key {request.key} and value {request.value}")

        if self.server.state == "Leader":
            log_entry = {"term": self.server.term, "update": {"command": 'SET', "key": request.key, "value": request.value}}
            self.server.log.append(log_entry)
            print(self.server.log)
            
            log_index = len(self.server.log)
            self.server.log_file.write(f"{log_entry['term']},{log_entry['update']['command']},{log_entry['update']['key']},{log_entry['update']['value']}\n")
            self.server.log_file.flush()
            
            reply = {"success": True}

        elif self.server.state == "Follower":
            channel = grpc.insecure_channel(SERVERS_INFO[self.server.leaderId])
            stub = pb2_grpc.RaftServiceStub(channel)
            message = pb2.KeyValMessage(key = request.key, value = request.value)

            try:
                response = stub.SetVal(message)
                reply = {"success": response.success}
            except grpc.RpcError as e:
                print(f"Server is not able to send the message to leader {self.server.leaderId} due to {e}")

        # print(reply)
        return pb2.OperationResponseMessage(success=reply["success"])

    def GetVal(self, request, context):
        if self.server.sleep:
            context.set_details("Server is sleeping")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            return pb2.ValResponseMessage()
        
        reply = {"success": False, "value": "None"}

        # Iterate over the log
        for entry in self.server.log:
            # Check if the log entry's 'update' dictionary contains the key
            if entry["update"]["command"] == 'SET' and entry["update"]["key"] == request.key:
                reply = {"success": True, "value": entry["update"]["value"]}
                break

        return pb2.ValResponseMessage(success=reply["success"], value=reply["value"])   
    
def serve():
    """Start the server."""
    print(f"Starting server {ID}")
    server_instance = Server(ID)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    handler_instance = Handler(server_instance)  # Pass the Server instance to Handler
    pb2_grpc.add_RaftServiceServicer_to_server(handler_instance, server)
    server.add_insecure_port(SERVERS_INFO[ID])
    server.start()
    print(f"Server {ID} listening on {SERVERS_INFO[ID]}")
    server.wait_for_termination()

def config():
    """Read the configuration file and store the server information."""
    with open("Config.txt", "r") as file:
        global SERVERS_INFO
        for line in file:
            server_info = line.split()
            SERVERS_INFO[int(server_info[0])] = server_info[1] + ":" + server_info[2]

def main():
    config()
    serve()

if __name__ == "__main__":
    main()

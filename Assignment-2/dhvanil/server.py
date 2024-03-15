import grpc
import random
import threading
import time
import sys
from concurrent import futures
import raft_pb2 as pb2
import raft_pb2_grpc as pb2_grpc

# Assuming SERVERS_INFO is filled with server id, address mappings
SERVERS_INFO = {
    1 : "localhost:50051",
    2 : "localhost:50052",
    3 : "localhost:50053",
    # 4 : "localhost:50054",
    # 5 : "localhost:50055",
}

ID = int(sys.argv[1])
LEASE_DURATION = 2.5
HEARTBEAT_INTERVAL = 1.0

class Server(pb2_grpc.RaftServiceServicer):
    def __init__(self):
        self.state = "Follower"
        self.term = 0
        self.id = ID
        self.voted_for = None
        self.log = []
        self.commitIndex = 0
        self.lastApplied = 0
        self.database = {}
        self.votes_received = 0
        self.election_timeout = None
        self.heartbeat_timer = None
        self.lock = threading.Lock()

        self.reset_election_timeout()

    def reset_election_timeout(self):
        with self.lock:
            if self.election_timeout:
                self.election_timeout.cancel()
            timeout = random.uniform(5, 10)
            self.election_timeout = threading.Timer(timeout, self.start_election)
            self.election_timeout.start()
            print(f"Server {self.id} reset election timeout to {timeout} seconds")

    def start_election(self):
        with self.lock:
            self.state = "Candidate"
            self.term += 1
            self.voted_for = self.id
            self.votes_received = 1  # Vote for self
            self.reset_election_timeout()

            for server_id in SERVERS_INFO:
                if server_id != self.id:
                    self.send_request_vote(server_id)

            print(f"Server {self.id} started election for term {self.term}")

    def send_request_vote(self, server_id):
        with self.lock:
            channel = grpc.insecure_channel(SERVERS_INFO[server_id])
            stub = pb2_grpc.RaftServiceStub(channel)
            last_log_index = len(self.log) - 1
            last_log_term = self.log[last_log_index][1] if self.log else 0
            response = stub.RequestVote(pb2.RequestVoteMessage(
                term=self.term,
                candidateId=self.id,
                lastLogIndex=last_log_index,
                lastLogTerm=last_log_term,
            ))
            if response.voteGranted and response.term == self.term:
                self.votes_received += 1
                if self.votes_received > len(SERVERS_INFO) // 2:
                    self.become_leader()
            print(f"Server {self.id} received {self.votes_received} votes for term {self.term}")

    def become_leader(self):
        with self.lock:
            self.state = "Leader"
            self.heartbeat_timer = threading.Timer(HEARTBEAT_INTERVAL, self.send_heartbeats)
            self.heartbeat_timer.start()
            print(f"Server {self.id} became leader for term {self.term}")

    def send_heartbeats(self):
        with self.lock:
            if self.state != "Leader":
                return
            for server_id in SERVERS_INFO:
                if server_id != self.id:
                    self.send_append_entries(server_id)
            self.heartbeat_timer = threading.Timer(HEARTBEAT_INTERVAL, self.send_heartbeats)
            self.heartbeat_timer.start()
            print(f"Server {self.id} sent heartbeats for term {self.term}")

    def send_append_entries(self, server_id):
        with self.lock:
            channel = grpc.insecure_channel(SERVERS_INFO[server_id])
            stub = pb2_grpc.RaftServiceStub(channel)
            prev_log_index = len(self.log) - 1
            prev_log_term = self.log[prev_log_index][1] if self.log else 0
            entries = self.log[prev_log_index + 1:] if prev_log_index + 1 < len(self.log) else []
            stub.AppendEntries(pb2.AppendEntriesMessage(
                term=self.term,
                leaderId=self.id,
                prevLogIndex=prev_log_index,
                prevLogTerm=prev_log_term,
                entries=[pb2.LogEntry(term=e[1], command=e[2]) for e in entries],
                leaderCommit=self.commitIndex,
            ))
            print(f"Server {self.id} sent append entries to {server_id} for term {self.term}")

    def RequestVote(self, request, context):
        with self.lock:
            vote_granted = False
            if request.term > self.term:
                self.state = "Follower"
                self.term = request.term
                self.voted_for = None
            if (self.voted_for is None or self.voted_for == request.candidateId) and \
               (not self.log or (self.log[-1][1] <= request.lastLogTerm and len(self.log)-1 <= request.lastLogIndex)):
                self.voted_for = request.candidateId
                vote_granted = True
                self.reset_election_timeout()
            return pb2.VoteResponseMessage(term=self.term, voteGranted=vote_granted)

    def AppendEntries(self, request, context):
        with self.lock:
            success = False
            if request.term >= self.term:
                self.state = "Follower"
                self.term = request.term
                self.reset_election_timeout()
                if request.prevLogIndex < len(self.log) and self.log[request.prevLogIndex][1] == request.prevLogTerm:
                    self.log = self.log[:request.prevLogIndex + 1] + [(i, e.term, e.command) for i, e in enumerate(request.entries, start=request.prevLogIndex + 1)]
                    success = True
                    if request.leaderCommit > self.commitIndex:
                        self.commitIndex = min(request.leaderCommit, len(self.log) - 1)
                        self.apply_committed_entries()
            return pb2.AppendEntriesResponseMessage(term=self.term, success=success)
        
    def apply_committed_entries(self):
        while self.commitIndex > self.lastApplied:
            self.lastApplied += 1
            _, _, command = self.log[self.lastApplied]
            key, value = command.split()[1:]
            self.database[key] = value
            print(f"Server {self.id} applied {command} to state machine")
        
    def SetVal(self, request, context):
        with self.lock:
            if self.state != "Leader":
                # Forward request to leader if known
                return pb2.OperationResponse(success=False, leaderId=str(self.leader_id))
            self.log.append((len(self.log), self.term, f"SET {request.key} {request.value}"))
            # Replicate to followers
            self.send_heartbeats()
            return pb2.OperationResponse(success=True, leaderId=str(self.id))
        
    def GetVal(self, request, context):
        with self.lock:
            # Ensure this server is the leader or read from leader's state if lease is valid
            if self.state != "Leader":
                return pb2.ValResponse(value="", leaderId=str(self.leader_id))
            return pb2.ValResponse(value=self.database.get(request.key, ""), leaderId=str(self.id))
        
    def run(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        pb2_grpc.add_RaftServiceServicer_to_server(self, server)
        # Add correct server address from SERVERS_INFO
        server.add_insecure_port(SERVERS_INFO[self.id])
        server.start()
        server.wait_for_termination()

if __name__ == "__main__":
    server = Server()
    server.run()

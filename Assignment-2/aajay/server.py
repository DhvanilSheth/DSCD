import time
import random
from concurrent import futures
import grpc
import raft_pb2
import raft_pb2_grpc
import threading 
# Constants for Raft timeouts
ELECTION_TIMEOUT_MIN = 150 / 1000  # 150ms
ELECTION_TIMEOUT_MAX = 300 / 1000  # 300ms
HEARTBEAT_INTERVAL = 50 / 1000  # 50ms

class RaftServer(raft_pb2_grpc.RaftServicer):
    def __init__(self, server_id, server_addresses):
        self.id = server_id
        self.peers = server_addresses
        self.term = 0
        self.voted_for = None
        self.logs = []
        self.commit_index = 0
        self.last_applied = 0
        self.next_index = {}
        self.match_index = {}
        self.state = 'Follower'
        self.leader_id = None
        self.leader_lease_expiry = time.time()

        # Initialize server state
        self.reset_election_timer()

    def reset_election_timer(self):
        self.election_timeout = time.time() + random.uniform(ELECTION_TIMEOUT_MIN, ELECTION_TIMEOUT_MAX)

    def become_leader(self):
        self.state = 'Leader'
        self.leader_id = self.id
        # Reset nextIndex and matchIndex for all peers
        for peer_id in self.peers:
            self.next_index[peer_id] = len(self.logs) + 1
            self.match_index[peer_id] = 0
        self.send_heartbeats()

    def become_follower(self, term):
        self.state = 'Follower'
        self.term = term
        self.voted_for = None
        self.leader_id = None
        self.reset_election_timer()

    def RequestVote(self, request, context):
        if request.term < self.term:
            return raft_pb2.RequestVoteResponse(term=self.term, voteGranted=False)

        if self.voted_for is None or self.voted_for == request.candidateId:
            self.voted_for = request.candidateId
            self.reset_election_timer()
            return raft_pb2.RequestVoteResponse(term=self.term, voteGranted=True)

        return raft_pb2.RequestVoteResponse(term=self.term, voteGranted=False)

    def AppendEntries(self, request, context):
        if request.term < self.term:
            return raft_pb2.AppendEntriesResponse(term=self.term, success=False)
        
        self.reset_election_timer()
        self.leader_id = request.leaderId
        # Assume successful append for simplicity, real implementation should check log consistency
        return raft_pb2.AppendEntriesResponse(term=self.term, success=True)

    def send_heartbeats(self):
        # Placeholder for sending heartbeats to all peers
        pass

    def check_election_timeout(self):
        if self.state != 'Leader' and time.time() >= self.election_timeout:
            self.start_election()

    def start_election(self):
        # Placeholder for election logic
        pass

    
    def election_timeout(self):
        return time.time() >= self.election_timeout

    def start_election(self):
        self.state = 'Candidate'
        self.term += 1
        self.voted_for = self.id
        self.votes_received = 1  # Vote for self
        self.reset_election_timer()
        print(f"Node {self.id} starting an election for term {self.term}.")

        # Request votes from all peers in parallel
        for peer_id in self.peers:
            if peer_id == self.id:
                continue
            threading.Thread(target=self.request_vote, args=(peer_id,)).start()

    def request_vote(self, peer_id):
        channel = grpc.insecure_channel(self.peers[peer_id])
        stub = raft_pb2_grpc.RaftStub(channel)
        response = stub.RequestVote(
            raft_pb2.RequestVoteRequest(
                term=self.term,
                candidateId=self.id,
                lastLogIndex=len(self.logs) - 1,
                lastLogTerm=self.logs[-1]['term'] if self.logs else 0,
            )
        )
        if response.voteGranted and response.term == self.term:
            self.votes_received += 1
            if self.votes_received > len(self.peers) / 2 and self.state == 'Candidate':
                self.become_leader()

    def send_heartbeats(self):
        if self.state != 'Leader':
            return

        for peer_id in self.peers:
            if peer_id == self.id:
                continue
            threading.Thread(target=self.send_heartbeat, args=(peer_id,)).start()

    def send_heartbeat(self, peer_id):
        channel = grpc.insecure_channel(self.peers[peer_id])
        stub = raft_pb2_grpc.RaftStub(channel)
        stub.AppendEntries(
            raft_pb2.AppendEntriesRequest(
                term=self.term,
                leaderId=self.id,
                prevLogIndex=len(self.logs) - 1,
                prevLogTerm=self.logs[-1]['term'] if self.logs else 0,
                entries=[],  # Empty for heartbeat
                leaderCommit=self.commit_index,
                leaderLeaseDuration=int(HEARTBEAT_INTERVAL * 5),  # Example lease duration
            )
        )

    def handle_append_entries(self, request, context):
        if request.term < self.term:
            return raft_pb2.AppendEntriesResponse(term=self.term, success=False)

        self.reset_election_timer()
        self.state = 'Follower'
        self.term = request.term
        self.leader_id = request.leaderId

        # Check log consistency
        if len(self.logs) < request.prevLogIndex or \
        (request.prevLogIndex > 0 and self.logs[request.prevLogIndex - 1]['term'] != request.prevLogTerm):
            return raft_pb2.AppendEntriesResponse(term=self.term, success=False)

        # Append any new entries
        index_to_start_appending = request.prevLogIndex
        for entry in request.entries:
            if index_to_start_appending < len(self.logs):
                if self.logs[index_to_start_appending]['term'] != entry.term:
                    self.logs = self.logs[:index_to_start_appending]  # Remove conflicting entries
            self.logs.append({'term': entry.term, 'key': entry.update.key, 'value': entry.update.value})
            index_to_start_appending += 1

        # Update commit index
        if request.leaderCommit > self.commit_index:
            self.commit_index = min(request.leaderCommit, len(self.logs))
            self.apply_log_entries()

        return raft_pb2.AppendEntriesResponse(term=self.term, success=True)

def serve(server_id, server_addresses):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raft_servicer = RaftServer(server_id, server_addresses)
    raft_pb2_grpc.add_RaftServicer_to_server(raft_servicer, server)

    server.add_insecure_port(server_addresses[server_id])
    server.start()
    try:
        while True:
            raft_servicer.check_election_timeout()
            time.sleep(0.1)
    except KeyboardInterrupt:
        server.stop(0)



if __name__ == '__main__':
    # Example usage: python server.py 0 'localhost:50051,localhost:50052,localhost:50053'
    import sys
    server_id = int(sys.argv[1])
    server_addresses = sys.argv[2].split(',')
    serve(server_id, server_addresses)

import sys
import os
import time
from threading import Thread, Timer, Lock
import random
import grpc
from concurrent import futures
import raft_pb2 as pb2
import raft_pb2_grpc as pb2_grpc
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')


# Global variables for server configuration
ID = int(sys.argv[1])  # Server ID passed as command-line argument
SERVERS_INFO = {}  # Dictionary to hold server information
LEASE_DURATION = 2.5  # Duration of the leader's lease
HEARTBEAT_INTERVAL = 1  # Interval between heartbeats

def config():
    """Read the configuration file and store the server information."""
    global SERVERS_INFO
    config_path = "Config.txt"  # Configuration file path
    if not os.path.exists(config_path):
        logging.error(f"Configuration file {config_path} not found.")
        sys.exit(1)
    with open(config_path, "r") as file:
        for line in file:
            server_info = line.strip().split()
            if len(server_info) != 3:
                logging.error(f"Invalid server information format in {config_path}.")
                sys.exit(1)
            SERVERS_INFO[int(server_info[0])] = f"{server_info[1]}:{server_info[2]}"

class Server:
    def __init__(self):
        self.state_lock = Lock()  # Lock for thread-safe state updates
        self.state = "Follower"  # Initial state
        self.term = 0  # Current term starts at 0
        self.id = ID  # Server ID from global variable
        self.votedFor = None  # Tracks who the server voted for
        self.leaderId = None  # ID of the current leader, if known
        self.timer = None  # Timer for election timeout
        self.database = {}  # Key-value store
        self.log = []  # Log of commands
        self.leaseExpiration = 0  # Time when the lease expires
        self.votesReceived = 0  # Votes received in the current election
        self.nextIndex = {}  # Index of the next log entry to send to each server
        self.matchIndex = {}  # Index of the highest log entry known to be replicated on each server
        self.commitIndex = 0  # Index of highest log entry known to be committed
        self.lastApplied = 0  # Index of highest log entry applied to state machine
        self.set_timeout()  # Initialize election timeout

    def set_timeout(self):
        """Set a random timeout for election, between 5 and 10 seconds."""
        timeout = random.uniform(5, 10)
        if self.timer:
            self.timer.cancel()
        self.timer = Timer(timeout, self.timeout_action)
        self.timer.start()

    def timeout_action(self):
        """Actions to take on timeout, based on current state."""
        with self.state_lock:
            if self.state == "Follower":
                self.become_candidate()
            elif self.state == "Candidate":
                self.start_election()

    def become_follower(self, term=None):
        """Transition to follower state and reset state as needed."""
        with self.state_lock:
            self.state = "Follower"
            if term is not None:
                self.term = term
            self.votedFor = None
            self.leaderId = None
            logging.info(f"Server {self.id} transitioned to Follower state.")
            self.set_timeout()  # Reset election timeout

    def become_candidate(self):
        """Transition to candidate state and start election."""
        with self.state_lock:
            self.state = "Candidate"
            self.term += 1  # Increment term
            self.votedFor = self.id  # Vote for self
            self.votesReceived = 1  # Reset vote count
            logging.info(f"Server {self.id} transitioned to Candidate state for term {self.term}.")
            self.start_election()

    def start_election(self):
        """Initiate election process."""
        with self.state_lock:
            self.votesReceived = 1  # Vote for self
            logging.info(f"Server {self.id} starting an election for term {self.term}.")
        
        # Request votes from all other servers in parallel
        for server_id, server_info in SERVERS_INFO.items():
            if server_id != self.id:
                Thread(target=self.request_vote, args=(server_id, server_info)).start()
        self.set_timeout()  # Reset election timeout to wait for vote responses

    def request_vote(self, server_id, server_info):
        """Sends a RequestVote RPC to another server."""
        logging.info(f"Server {self.id} requesting vote from server {server_id} for term {self.term}.")
        with grpc.insecure_channel(server_info) as channel:
            stub = pb2_grpc.RaftServiceStub(channel)
            response = stub.RequestVote(pb2.VoteRequestMessage(
                term=self.term,
                candidateId=self.id,
                lastLogIndex=len(self.log),
                lastLogTerm=self.log[-1]['term'] if self.log else 0,
                oldLeaderLeaseDuration=self.get_lease_duration()
            ))
            self.receive_vote(response.term, response.voteGranted, response.oldLeaderLeaseDuration)

    def receive_vote(self, term, voteGranted, oldLeaderLeaseDuration):
        """Processes a received vote."""
        with self.state_lock:
            if term == self.term and voteGranted:
                self.votesReceived += 1
                if self.votesReceived > len(SERVERS_INFO) / 2:
                    self.become_leader()
            elif term > self.term:
                self.become_follower(term)
            self.update_lease(oldLeaderLeaseDuration)

    def become_leader(self):
        """Transitions the server to the leader state and begins sending heartbeats."""
        with self.state_lock:
            self.state = "Leader"
            self.leaderId = self.id
            logging.info(f"Server {self.id} became the leader for term {self.term}.")
            self.nextIndex = {server_id: len(self.log) + 1 for server_id in SERVERS_INFO}
            self.matchIndex = {server_id: 0 for server_id in SERVERS_INFO}
            self.send_heartbeats()

    def send_heartbeats(self):
        """Sends heartbeats to all followers to assert leadership."""
        logging.info(f"Leader {self.id} sending heartbeats.")
        for server_id, server_info in SERVERS_INFO.items():
            if server_id != self.id:
                with grpc.insecure_channel(server_info) as channel:
                    stub = pb2_grpc.RaftServiceStub(channel)
                    response = stub.AppendEntries(pb2.AppendEntriesRequestMessage(
                        term=self.term,
                        leaderId=self.id,
                        prevLogIndex=len(self.log),
                        prevLogTerm=self.log[-1]['term'] if self.log else 0,
                        entries=[],
                        leaderCommit=self.commitIndex,
                        oldLeaderLeaseDuration=self.get_lease_duration()
                    ))
                    if response.term > self.term:
                        self.become_follower(response.term)
                    self.update_lease(response.oldLeaderLeaseDuration)

    def get_lease_duration(self):
        """Calculates the remaining lease duration."""
        return max(0, self.leaseExpiration - time.time())

    def update_lease(self, oldLeaderLeaseDuration):
        """Updates the lease expiration time."""
        self.leaseExpiration = time.time() + oldLeaderLeaseDuration

    def serve(self):
        """Starts the gRPC server and listens for Raft RPCs."""
        self.grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        pb2_grpc.add_RaftServiceServicer_to_server(RaftService(self), self.grpc_server)
        # Adjust address binding based on SERVERS_INFO global dict
        self.grpc_server.add_insecure_port(SERVERS_INFO[self.id])
        logging.info(f"Server {self.id} listening on {SERVERS_INFO[self.id]}")
        self.grpc_server.start()
        self.grpc_server.wait_for_termination()

    def shutdown(self):
        """Shuts down the gRPC server."""
        logging.info(f"Shutting down server {self.id}.")
        try:
            self.grpc_server.stop(None)
        except Exception as e:
            logging.exception("An error occurred while shutting down")


class RaftService(pb2_grpc.RaftServiceServicer):
    def __init__(self, server):
        self.server = server

    def RequestVote(self, request, context):
        with self.server.state_lock:
            term = request.term
            candidateId = request.candidateId
            lastLogIndex = request.lastLogIndex
            lastLogTerm = request.lastLogTerm

            voteGranted = False
            currentTerm = self.server.term
            # Check term and log freshness
            if (term > currentTerm or (term == currentTerm and self.server.votedFor in [None, candidateId])):
                if lastLogIndex >= len(self.server.log) and (len(self.server.log) == 0 or lastLogTerm >= self.server.log[-1]['term']):
                    self.server.votedFor = candidateId
                    voteGranted = True
                    self.server.set_timeout()  # Reset election timeout

            response = pb2.VoteResponseMessage(
                term=currentTerm,
                voteGranted=voteGranted,
                oldLeaderLeaseDuration=self.server.get_lease_duration()
            )
            return response

    def AppendEntries(self, request, context):
        with self.server.state_lock:
            term = request.term
            leaderId = request.leaderId
            prevLogIndex = request.prevLogIndex
            prevLogTerm = request.prevLogTerm
            entries = request.entries
            leaderCommit = request.leaderCommit

            success = False
            if term >= self.server.term:
                self.server.become_follower(term)  # Update term and transition to follower if necessary
                self.server.update_lease(request.oldLeaderLeaseDuration)  # Update lease expiration time
                if prevLogIndex == 0 or (prevLogIndex <= len(self.server.log) and self.server.log[prevLogIndex - 1]['term'] == prevLogTerm):
                    success = True
                    # Append new entries not already in the log
                    self.server.log = self.server.log[:prevLogIndex] + entries

                # Update commit index
                if leaderCommit > self.server.commitIndex:
                    self.server.commitIndex = min(leaderCommit, len(self.server.log))

            response = pb2.AppendEntriesResponseMessage(
                term=self.server.term,
                success=success,
                oldLeaderLeaseDuration=self.server.get_lease_duration()
            )
            return response

    def GetLeader(self, request, context):
        """Returns the current leader's information if known."""
        # This is a simplification. Ideally, you'd have a mechanism to find the current leader.
        with self.server.state_lock:
            if self.server.leaderId is not None:
                return pb2.LeaderMessage(leaderId=self.server.leaderId, leaderAddress=SERVERS_INFO.get(self.server.leaderId, ""))
            else:
                return pb2.LeaderMessage(leaderId=-1, leaderAddress="")

    def SetVal(self, request, context):
        """Handles a SetVal RPC from a client, assuming current server is the leader."""
        with self.server.state_lock:
            if self.server.state == "Leader":
                # Simplified log append for demonstration
                self.server.log.append({"key": request.key, "value": request.value})
                # Here you would also need to replicate this log entry to the followers and wait for a majority to acknowledge
                return pb2.SetValResponseMessage(success=True)
            else:
                return pb2.SetValResponseMessage(success=False)

    def GetVal(self, request, context):
        """Handles a GetVal RPC from a client."""
        with self.server.state_lock:
            value = self.server.database.get(request.key)
            return pb2.GetValResponseMessage(value=value if value else "")

def main():
    config()  # Load server configuration
    server = Server()  # Create a Raft server instance
    server.serve()  # Start serving

if __name__ == "__main__":
    main()
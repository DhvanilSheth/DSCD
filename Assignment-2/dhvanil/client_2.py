import grpc
import raft_pb2 as pb2
import raft_pb2_grpc as pb2_grpc
import os
import sys


SERVERS_INFO = {}  # Dictionary to hold server information

def config():
    """Read the configuration file and store the server information."""
    global SERVERS_INFO
    config_path = "Config.txt"  # Configuration file path
    if not os.path.exists(config_path):
        print(f"Configuration file {config_path} not found.")
        sys.exit(1)
    with open(config_path, "r") as file:
        for line in file:
            server_info = line.strip().split()
            if len(server_info) != 3:
                print(f"Invalid server information format in {config_path}.")
                sys.exit(1)
            SERVERS_INFO[int(server_info[0])] = f"{server_info[1]}:{server_info[2]}"

def connect(server_info):
    """Establish a connection to a server."""
    return grpc.insecure_channel(server_info)

def get_leader():
    """Find the leader of the Raft cluster."""
    for server_id, server_info in SERVERS_INFO.items():
        channel = grpc.insecure_channel(server_info)
        stub = pb2_grpc.RaftServiceStub(channel)
        try:
            response = stub.GetLeader(pb2.EmptyMessage())
            if response.leaderId != -1:
                print(f"Leader is server {response.leaderId} at {server_info}")
                channel.close()  # Properly close the channel
                return stub, server_info
        except grpc.RpcError as e:
            print(f"Failed to get leader from server {server_id}: {e}")
        channel.close()  # Ensure channel closure in case of failure
    print("No leader found.")
    return None, None

def getVal(key):
    """Get a value from the Raft cluster."""
    leader, leader_info = get_leader()
    if leader is not None:
        response = leader.GetVal(pb2.GetValRequestMessage(key=key))
        if response.value is not None:
            print(f"Value: {response.value}")
        else:
            print("Key not found.")

def setVal(key, value):
    """Set a value in the Raft cluster."""
    leader, leader_info = get_leader()
    if leader is not None:
        response = leader.SetVal(pb2.SetValRequestMessage(key=key, value=value))
        if response.success:
            print("Value set successfully.")
        else:
            print("Failed to set value.")

def client():
    """Interactive client for communicating with the Raft cluster."""
    print("Raft Client Started. Type 'quit' to exit.")
    while True:
        cmd = input("> ").strip().lower()
        if cmd == "quit":
            print("Client terminated.")
            break
        elif cmd.startswith("getval "):
            parts = cmd.split(maxsplit=1)
            if len(parts) != 2:
                print("Invalid command. Use 'getval <key>'.")
                continue
            _, key = parts
            getVal(key)
        elif cmd.startswith("setval "):
            parts = cmd.split(maxsplit=2)
            if len(parts) != 3:
                print("Invalid command. Use 'setval <key> <value>'.")
                continue
            _, key, value = parts
            setVal(key, value)
        elif cmd == "getleader":
            get_leader()
        else:
            print("Unknown command. Use 'getval', 'setval', or 'getleader'.")

if __name__ == "__main__":
    config()  # Load server configuration
    client()  # Start client
import sys
import grpc
import raft_pb2 as pb2
import raft_pb2_grpc as pb2_grpc

SERVERS_INFO = {0 : "localhost:50051", 1 : "localhost:50052", 2 : "localhost:50053"}

def connect():
    """Attempt to connect to one of the Raft servers."""
    for id, address in SERVERS_INFO.items():
        channel = grpc.insecure_channel(address)
        stub = pb2_grpc.RaftServiceStub(channel)
        # Attempt to get the status or leader to ensure the connection is successful
        try:
            response = stub.GetLeader(pb2.EmptyMessage())
            print(f'Connected to server {id} at {address}')
            return stub
        except grpc.RpcError as e:
            print(f"Failed to connect to server {id} at {address}: {e}")
    print("No servers are available.")
    return None

def get_leader():
    """Get the current leader of the Raft cluster."""
    stub = connect()
    if stub:
        try:
            response = stub.GetLeader(pb2.EmptyMessage())
            if response.leader != -1:
                print(f'Current leader ID: {response.leader} at {response.address}')
            else:
                print("Leader information is currently unavailable.")
        except grpc.RpcError as e:
            print(f"Error getting leader information: {e}")

def getVal(key):
    """Get the value for a given key from the Raft cluster."""
    stub = connect()
    if stub:
        try:
            response = stub.GetVal(pb2.KeyMessage(key=key))
            if response.success:
                print(f'{key} = {response.value}')
            else:
                print(f"Failed to retrieve value for key: {key}")
        except grpc.RpcError as e:
            print(f"Error getting value for key {key}: {e}")

def setVal(key, value):
    """Set the value for a given key in the Raft cluster."""
    stub = connect()
    if stub:
        try:
            response = stub.SetVal(pb2.KeyValMessage(key=key, value=value))
            if response.success:
                print(f'Successfully set {key} = {value}')
            else:
                print(f"Failed to set value for key: {key}")
        except grpc.RpcError as e:
            print(f"Error setting value for key {key}: {e}")

def configuration():
    """Load server configurations from a configuration file."""
    with open('Config.conf', 'r') as f:
        global SERVERS_INFO
        for line in f:
            if line.strip():
                id, address, port = line.split()
                SERVERS_INFO[int(id)] = f"{address}:{port}"

def client():
    """Interactive client for sending commands to the Raft cluster."""
    print("Raft Client Started. Type 'quit' to exit.")
    while True:
        try:
            input_buffer = input("> ").strip()
            if not input_buffer:
                continue

            parts = input_buffer.split()
            command = parts[0]
            args = parts[1:]

            if command == "getleader":
                get_leader()
            elif command == "getval" and len(args) == 1:
                getVal(args[0])
            elif command == "setval" and len(args) == 2:
                setVal(args[0], args[1])
            elif command == "quit":
                print("Client Terminated.")
                break
            else:
                print("Unsupported command.")
        except KeyboardInterrupt:
            print("\nClient Terminated.")
            break

if __name__ == "__main__":
    configuration()
    client()

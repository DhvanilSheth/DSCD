import grpc
import raft_pb2 as pb2
import raft_pb2_grpc as pb2_grpc

# Assuming SERVERS_INFO is loaded from a configuration similar to the server setup
SERVERS_INFO = {0: "localhost:50051", 1: "localhost:50052", 2: "localhost:50053"}

def connect():
    """Attempt to connect to the Raft cluster and return the stub of the leader."""
    for id, address in SERVERS_INFO.items():
        channel = grpc.insecure_channel(address)
        stub = pb2_grpc.RaftServiceStub(channel)
        try:
            response = stub.GetLeader(pb2.EmptyMessage())
            if response.leaderId != -1:
                print(f'Connected to leader {response.leaderId} at {address}')
                return stub, response.leaderId
            else:
                print(f"Server {id} at {address} is not the leader.")
        except grpc.RpcError as e:
            print(f"Failed to connect to server {id} at {address}: {e}")
    print("Unable to find the leader or connect to the cluster.")
    return None, None

def get_leader():
    """Get the current leader of the Raft cluster."""
    _, leader_id = connect()
    if leader_id is not None:
        print(f'Current leader ID: {leader_id}')

def getVal(key):
    """Get the value for a given key from the Raft cluster."""
    stub, _ = connect()
    if stub:
        try:
            response = stub.GetVal(pb2.KeyMessage(key=key))
            if response.success:
                print(f'Value for {key}: {response.value}')
            else:
                print(f"Key '{key}' not found.")
        except grpc.RpcError as e:
            print(f"Error getting value for key '{key}': {e}")

def setVal(key, value):
    """Set the value for a given key in the Raft cluster."""
    stub, _ = connect()
    if stub:
        try:
            response = stub.SetVal(pb2.KeyValMessage(key=key, value=value))
            if response.success:
                print(f'Successfully set {key} = {value}')
            else:
                print(f"Failed to set value for key: {key}")
        except grpc.RpcError as e:
            print(f"Error setting value for key '{key}': {e}")

def client():
    """Interactive client for communicating with the Raft cluster."""
    print("Raft Client Started. Type 'quit' to exit.")
    while True:
        cmd = input("> ").strip().lower()
        if cmd == "quit":
            print("Client terminated.")
            break
        elif cmd.startswith("getval "):
            _, key = cmd.split(maxsplit=1)
            getVal(key)
        elif cmd.startswith("setval "):
            _, rest = cmd.split(maxsplit=1)
            key, value = rest.split(maxsplit=1)
            setVal(key, value)
        elif cmd == "getleader":
            get_leader()
        else:
            print("Unknown command. Use 'getval', 'setval', or 'getleader'.")

if __name__ == "__main__":
    client()
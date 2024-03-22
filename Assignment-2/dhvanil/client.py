import grpc
import raft_pb2 as pb2
import raft_pb2_grpc as pb2_grpc

# Assuming SERVERS_INFO is loaded from a configuration similar to the server setup
SERVERS_INFO = {0: "localhost:50051", 1: "localhost:50052", 2: "localhost:50053", 3: "localhost:50054", 4: "localhost:50055"}
leader_info = {"stub": None, "id": None}
 
def connect():
    """Attempt to connect to the Raft cluster and return the stub of the leader."""
    # if leader_info["stub"] and leader_info["id"]:
    #     return leader_info["stub"], leader_info["id"]

    for id, address in SERVERS_INFO.items():
        try:
            channel = grpc.insecure_channel(address)
            stub = pb2_grpc.RaftServiceStub(channel)
            response = stub.GetLeader(pb2.EmptyMessage())
            leader_address = response.leaderAddress
            leader_id = response.leaderId
            if leader_address == "empty":
                print(f"Server {id} is not the leader.")
            else:
                print(f"Found leader {leader_id} at {leader_address}")
                leader_channel = grpc.insecure_channel(leader_address)
                leader_stub = pb2_grpc.RaftServiceStub(leader_channel)
                leader_info["stub"] = leader_stub
                leader_info["id"] = leader_id
                return leader_stub, leader_id
                
        except grpc.RpcError:
            print(f"Failed to connect to server {id} at {address}")
    
    print("Unable to find the leader or connect to the cluster.")
    return None, None

def get_leader():
    """Get the current leader of the Raft cluster."""
    leader_info["stub"], leader_info["id"] = None, None  # Reset the leader info
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
                print(f"Set value for key '{key}' to '{value}'.")
            else:
                print(f"Failed to set value for key '{key}'.")
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
        elif cmd.startswith("get "):
            _, key = cmd.split(maxsplit=1)
            getVal(key)
        elif cmd.startswith("set "):
            _, rest = cmd.split(maxsplit=1)
            key, value = rest.split(maxsplit=1)
            setVal(key, value)
        elif cmd == "leader":
            get_leader()
        else:
            print("Unknown command. Use 'GET', 'SET', or 'LEADER'.")

if __name__ == "__main__":
    client()
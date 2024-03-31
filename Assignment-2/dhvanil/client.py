import grpc
import raft_pb2
import raft_pb2_grpc
import sys

def find_leader(node_addresses):
    for node_id, node_address in node_addresses.items():
        with grpc.insecure_channel(node_address) as channel:
            stub = raft_pb2_grpc.RaftStub(channel)
            try:
                response = stub.ServeClient(raft_pb2.ServeClientArgs(Request="GET __leader__"))
                if response.Success:
                    print(f"Found and connected to leader: {response.LeaderID}")
                    return response.LeaderID
            except grpc.RpcError:
                continue
    return None

def handle_client_requests(node_address, leader_id):
    with grpc.insecure_channel(node_address) as channel:
        stub = raft_pb2_grpc.RaftStub(channel)
        while True:
            print("Enter your request (get, set) <key> <value> or 'quit' to exit")
            request = input("> ")

            if request.lower() == 'quit':
                print("Ending Client")
                sys.exit(0)
            
            try:
                response = stub.ServeClient(raft_pb2.ServeClientArgs(Request=request))

                if response.Success:
                    if response.Data == "":
                        print("Changes applied successfully")
                    else:
                        print(f"Data received: {response.Data}")

                else:
                    print(f"Old leader not found! Attempting to connect to new leader")
                    new_leader_id = None if response.LeaderID == 'None' else response.LeaderID

                    if new_leader_id is not None:
                        print("New leader ID is:", new_leader_id)
                    return new_leader_id
                
            except grpc.RpcError as e:
                print(f"Error occurred: {e}")
                return None

def run_client(node_addresses):
    leader_id = None
    while True:
        if leader_id is None:
            leader_id = find_leader(node_addresses)
        else:
            leader_id = handle_client_requests(node_addresses[int(leader_id)], leader_id)

if __name__ == "__main__":
    node_addresses = {
        0: "localhost:50050",
        1: "localhost:50051",
        2: "localhost:50052",
        3: "localhost:50053",
        4: "localhost:50054",
    }
    # node_addresses = {
    #     0: "10.128.0.2:50050",
    #     1: "10.128.0.3:50051",
    #     2: "10.128.0.4:50052",
    #     3: "10.128.0.5:50053",
    #     4: "10.128.0.6:50054",
    # }
    run_client(node_addresses)
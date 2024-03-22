import grpc
import raft_pb2
import raft_pb2_grpc

def run_client(node_address_mapping):
    leader_node_id = None
    while True:
        if leader_node_id is None:
            for node_id, node_address in node_address_mapping.items():
                with grpc.insecure_channel(node_address) as channel:
                    raft_stub = raft_pb2_grpc.RaftStub(channel)
                    try:
                        response = raft_stub.ServeClient(raft_pb2.ServeClientArgs(Request="GET __leader__"))
                        if response.Success:
                            leader_node_id = response.LeaderID
                            print(f"Connected to leader: {leader_node_id}")
                            break
                    except grpc.RpcError as e:
                        continue
        else:
            with grpc.insecure_channel(node_address_mapping[int(leader_node_id)]) as channel:
                raft_stub = raft_pb2_grpc.RaftStub(channel)
                while True:
                    client_request = input("Enter command (GET <key> or SET <key> <value>): ")
                    try:
                        response = raft_stub.ServeClient(raft_pb2.ServeClientArgs(Request=client_request))
                        if response.Success:
                            print(f"Response: {response.Data}")
                        else:
                            print(f"Leader changed. Connecting to new leader.")
                            leader_node_id = None if response.LeaderID == 'None' else response.LeaderID
                            if leader_node_id is not None:
                                print("New leader ID is:", leader_node_id)
                            break
                    except grpc.RpcError as e:
                        print(f"Error occurred: {e}")
                        leader_node_id = None
                        break

if __name__ == "__main__":
    node_address_mapping = {
        0: "localhost:50050",
        1: "localhost:50051",
        2: "localhost:50052",
        3: "localhost:50053",
        4: "localhost:50054",
        5: "localhost:50055",
    }
    run_client(node_address_mapping)
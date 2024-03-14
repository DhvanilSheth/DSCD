import grpc
import raft_pb2
import raft_pb2_grpc

class RaftClient:
    def __init__(self, server_addresses):
        self.server_addresses = server_addresses

    def find_leader(self):
        for address in self.server_addresses:
            try:
                channel = grpc.insecure_channel(address)
                stub = raft_pb2_grpc.RaftStub(channel)
                response = stub.GetLeader(raft_pb2.EmptyMessage())
                if response.leader != -1:
                    return response.address
            except grpc.RpcError:
                continue
        return None

    def set_value(self, key, value, retry_count=3):
        leader_address = self.find_leader()
        if leader_address:
            try:
                channel = grpc.insecure_channel(leader_address)
                stub = raft_pb2_grpc.RaftStub(channel)
                response = stub.SetVal(raft_pb2.KeyValMessage(key=key, value=value))
                return response.success
            except grpc.RpcError as e:
                if retry_count > 0:
                    print(f"Failed to set value, retrying... Error: {e}")
                    return self.set_value(key, value, retry_count - 1)
                else:
                    print("Failed to set value after retries.")
        else:
            print("Leader not found. Cannot set value.")
        return False


    def get_value(self, key):
        leader_address = self.find_leader()
        if leader_address:
            try:
                channel = grpc.insecure_channel(leader_address)
                stub = raft_pb2_grpc.RaftStub(channel)
                response = stub.GetVal(raft_pb2.KeyMessage(key=key))
                if response.success:
                    return response.value
                else:
                    return "Key not found."
            except grpc.RpcError:
                print("Failed to get value. Trying to find a new leader.")
                return self.get_value(key)
        else:
            print("Leader not found. Cannot get value.")
            return None
        



if __name__ == "__main__":
    client = RaftClient(['localhost:50051', 'localhost:50052', 'localhost:50053'])
    # Test setting a value
    success = client.set_value("testKey", "testValue")
    print(f"Set operation success: {success}")

    # Test getting a value
    value = client.get_value("testKey")
    print(f"Get operation returned: {value}")

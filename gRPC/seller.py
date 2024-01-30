import grpc
import shopping_platform_pb2
import shopping_platform_pb2_grpc

class SellerClient:
    def __init__(self, address, uuid):
        self.address = address
        self.uuid = uuid
        channel = grpc.insecure_channel('localhost:50051')
        self.stub = shopping_platform_pb2_grpc.MarketServiceStub(channel)

    def register_seller(self):
        try:
            request = shopping_platform_pb2.RegisterSellerRequest(address=self.address, uuid=self.uuid)
            response = self.stub.RegisterSeller(request)
            print(response.message)
        except grpc.RpcError as e:
            print(f"RPC failed: {e}")

    def sell_item(self, item):
        try:
            request = shopping_platform_pb2.SellerItemOperationRequest(
                uuid=self.uuid,
                address=self.address,
                item=item
            )
            response = self.stub.SellItem(request)
            print(response.message)
        except grpc.RpcError as e:
            print(f"RPC failed: {e}")

    def update_item(self, item_id, updated_item):
        try:
            request = shopping_platform_pb2.SellerItemOperationRequest(
                uuid=self.uuid,
                address=self.address,
                item=updated_item
            )
            request.item.id = item_id  # Set the item ID to be updated
            response = self.stub.UpdateItem(request)
            print(response.message)
        except grpc.RpcError as e:
            print(f"RPC failed: {e}")

    def delete_item(self, item_id):
        try:
            request = shopping_platform_pb2.SellerItemOperationRequest(
                uuid=self.uuid,
                address=self.address,
                item=shopping_platform_pb2.Item(id=item_id)
            )
            response = self.stub.DeleteItem(request)
            print(response.message)
        except grpc.RpcError as e:
            print(f"RPC failed: {e}")

    def display_items(self):
        try:
            request = shopping_platform_pb2.DisplayItemsRequest(address=self.address, uuid=self.uuid)
            responses = self.stub.DisplaySellerItems(request)
            print("Market prints: Display Items request from", self.address)
            for item in responses:
                print("Item ID:", item.id)
                print("Price:", item.price)
                print("Name:", item.name)
                print("Category:", item.category)
                print("Description:", item.description)
                print("Quantity Remaining:", item.quantity)
                print("Seller:", self.address)
                print("Rating:", item.rating, "/ 5")
                print("-")
        except grpc.RpcError as e:
            print(f"RPC failed: {e}")

if __name__ == '__main__':
    seller = SellerClient('192.13.188.178:50051', 'your-uuid')
    # Example usage:
    # seller.register_seller()
    # item = shopping_platform_pb2.Item(
    #     name="Example Product",
    #     category=shopping_platform_pb2.ELECTRONICS,
    #     quantity=10,
    #     description="Example Description",
    #     price=100.00
    # )
    # seller.sell_item(item)

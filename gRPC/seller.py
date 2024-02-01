import grpc
import shopping_platform_pb2
import shopping_platform_pb2_grpc
import uuid

class SellerClient:
    def __init__(self, address):
        channel = grpc.insecure_channel(address)
        self.stub = shopping_platform_pb2_grpc.MarketServiceStub(channel)
        self.uuid = str(uuid.uuid1())
        self.seller_address = address

    def register_seller(self):
        request = shopping_platform_pb2.RegisterSellerRequest(
            seller_address=self.seller_address,
            uuid=self.uuid
        )
        try:
            response = self.stub.RegisterSeller(request)
            print(f"RegisterSeller response: {response.message}")
        except grpc.RpcError as e:
            print(f"RegisterSeller failed with {e.code()}: {e.details()}")

    def sell_item(self, name, category, quantity, description, price):
        request = shopping_platform_pb2.SellerItemOperationRequest(
            uuid=self.uuid,
            name=name,
            category=category,
            quantity=quantity,
            description=description,
            price=price
        )
        try:
            response = self.stub.SellItem(request)
            print(f"SellItem response: {response.message}")
        except grpc.RpcError as e:
            print(f"SellItem failed with {e.code()}: {e.details()}")

    def update_item(self, item_id, price, quantity):
        request = shopping_platform_pb2.SellerItemOperationRequest(
            uuid=self.uuid,
            item_id=item_id,
            price=price,
            quantity=quantity
        )
        try:
            response = self.stub.UpdateItem(request)
            print(f"UpdateItem response: {response.message}")
        except grpc.RpcError as e:
            print(f"UpdateItem failed with {e.code()}: {e.details()}")

    def delete_item(self, item_id):
        request = shopping_platform_pb2.SellerItemOperationRequest(
            uuid=self.uuid,
            item_id=item_id
        )
        try:
            response = self.stub.DeleteItem(request)
            print(f"DeleteItem response: {response.message}")
        except grpc.RpcError as e:
            print(f"DeleteItem failed with {e.code()}: {e.details()}")

    def display_items(self):
        request = shopping_platform_pb2.DisplayItemsRequest(
            seller_address=self.seller_address,
            uuid=self.uuid
        )
        try:
            for item in self.stub.DisplaySellerItems(request):
                print(f"DisplayItems response - Item ID: {item.id}, Price: ${item.price}, Name: {item.name}, "
                      f"Category: {shopping_platform_pb2.Category.Name(item.category)}, "
                      f"Description: {item.description}, Quantity Remaining: {item.quantity}, "
                      f"Rating: {item.rating} / 5")
        except grpc.RpcError as e:
            print(f"DisplaySellerItems failed with {e.code()}: {e.details()}")

# Entry point for the seller client
def run():
    seller = SellerClient('localhost:50051')
    print("Seller client is running...")
    seller.register_seller()
    # Perform other operations such as sell_item, update_item, delete_item, display_items as needed
    # Example usage (uncomment to use):
    # seller.sell_item("Laptop", shopping_platform_pb2.ELECTRONICS, 10, "Latest model", 999.99)
    # seller.update_item(1, 899.99, 8)
    # seller.delete_item(1)
    # seller.display_items()

if __name__ == '__main__':
    run()
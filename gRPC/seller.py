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
            print(response.message)
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
            print(response.message)
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
            print(response.message)
        except grpc.RpcError as e:
            print(f"UpdateItem failed with {e.code()}: {e.details()}")

    def delete_item(self, item_id):
        request = shopping_platform_pb2.SellerItemOperationRequest(
            uuid=self.uuid,
            item_id=item_id
        )
        try:
            response = self.stub.DeleteItem(request)
            print(response.message)
        except grpc.RpcError as e:
            print(f"DeleteItem failed with {e.code()}: {e.details()}")

    def display_items(self):
        request = shopping_platform_pb2.DisplayItemsRequest(
            seller_address=self.seller_address,
            uuid=self.uuid
        )
        try:
            for item in self.stub.DisplaySellerItems(request):
                print(f"Item ID: {item.id}, Price: ${item.price}, Name: {item.name}, "
                      f"Category: {item.category}, Description: {item.description}, "
                      f"Quantity Remaining: {item.quantity}, Rating: {item.rating} / 5")
        except grpc.RpcError as e:
            print(f"DisplaySellerItems failed with {e.code()}: {e.details()}")

def run():
    seller = SellerClient('localhost:50051')
    seller.register_seller()
    # Perform other operations such as sell_item, update_item, delete_item, display_items as needed
    

if __name__ == '__main__':
    run()

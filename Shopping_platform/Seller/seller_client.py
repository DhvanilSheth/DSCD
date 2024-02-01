import grpc
import uuid
import shopping_pb2
import shopping_pb2_grpc

# The seller's address and uuid should be unique for each instance of the seller client
seller_address = '192.168.1.1:50051'
seller_uuid = str(uuid.uuid4())

def register_seller(stub):
    response = stub.RegisterSeller(shopping_pb2.RegisterSellerRequest(
        address=seller_address, uuid=seller_uuid))
    print(f"Seller prints: {response.message}")

def sell_item(stub):
    item = shopping_pb2.Item(
        name="Example Product",
        category=shopping_pb2.ELECTRONICS,
        description="An example item description",
        quantity=10,
        price=99.99,
        seller_address=seller_address
    )
    response = stub.SellItem(item)
    print(f"Seller prints: {response.message} with item id {response.item_id}")

# You should implement the UpdateItem, DeleteItem, and DisplaySellerItems in a similar way

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = shopping_pb2_grpc.MarketStub(channel)
        print("-------------- RegisterSeller --------------")
        register_seller(stub)

        print("-------------- SellItem --------------")
        sell_item(stub)

        # Call the other methods here

if __name__ == '__main__':
    run()

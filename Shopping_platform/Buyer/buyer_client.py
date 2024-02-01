import grpc
import shopping_pb2
import shopping_pb2_grpc

# The buyer's address should be unique for each instance of the buyer client
buyer_address = '192.168.1.2:50052'

def search_item(stub, name, category):
    for item in stub.SearchItem(shopping_pb2.SearchItemRequest(name=name, category=category)):
        print(f"Item ID: {item.id}, Price: ${item.price}, Name: {item.name}, Category: {item.category}, "
              f"Description: {item.description}, Quantity Remaining: {item.quantity}, Rating: {item.rating} / 5  |  "
              f"Seller: {item.seller_address}")

def buy_item(stub, item_id, quantity):
    response = stub.BuyItem(shopping_pb2.BuyItemRequest(
        item_id=item_id, quantity=quantity, buyer_address=buyer_address))
    print(f"Buyer prints: {response.message}")

# Implement AddToWishList and RateItem similarly to buy_item

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = shopping_pb2_grpc.MarketStub(channel)
        print("-------------- SearchItem --------------")
        search_item(stub, name="iPhone", category=shopping_pb2.ELECTRONICS)

        print("-------------- BuyItem --------------")
        buy_item(stub, item_id=1, quantity=1)

        # Call AddToWishList and RateItem here

if __name__ == '__main__':
    run()

import grpc
import shopping_platform_pb2
import shopping_platform_pb2_grpc

class BuyerClient:
    def __init__(self, address):
        self.address = address
        channel = grpc.insecure_channel('localhost:50051')
        self.stub = shopping_platform_pb2_grpc.MarketServiceStub(channel)

    def search_item(self, name, category):
        try:
            search_request = shopping_platform_pb2.SearchItemRequest(name=name, category=category)
            responses = self.stub.SearchItem(search_request)
            for item in responses:
                print(f"Item ID: {item.id}, Price: ${item.price}, Name: {item.name}, Category: {item.category.name}")
                print(f"Description: {item.description}")
                print(f"Quantity Remaining: {item.quantity}")
                print(f"Rating: {item.rating} / 5 | Seller: {item.seller_address}")
                print("-")
        except grpc.RpcError as e:
            print(f"RPC failed: {e}")

    def buy_item(self, item_id, quantity):
        try:
            buy_request = shopping_platform_pb2.BuyItemRequest(item_id=item_id, quantity=quantity, buyer_address=self.address)
            response = self.stub.BuyItem(buy_request)
            print(response.message)
        except grpc.RpcError as e:
            print(f"RPC failed: {e}")

    def add_to_wishlist(self, item_id):
        try:
            wishlist_request = shopping_platform_pb2.WishlistRequest(item_id=item_id, buyer_address=self.address)
            response = self.stub.AddToWishlist(wishlist_request)
            print(response.message)
        except grpc.RpcError as e:
            print(f"RPC failed: {e}")

    def rate_item(self, item_id, rating):
        try:
            rate_request = shopping_platform_pb2.RateItemRequest(item_id=item_id, rating=rating, buyer_address=self.address)
            response = self.stub.RateItem(rate_request)
            print(response.message)
        except grpc.RpcError as e:
            print(f"RPC failed: {e}")

if __name__ == '__main__':
    buyer = BuyerClient('120.13.188.178:50051')
    # Example usage:
    # buyer.search_item('iPhone', shopping_platform_pb2.ELECTRONICS)

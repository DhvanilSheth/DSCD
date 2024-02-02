import grpc
import shopping_platform_pb2
import shopping_platform_pb2_grpc

class BuyerClient:
    def __init__(self, address):
        self.channel = grpc.insecure_channel(address)
        self.stub = shopping_platform_pb2_grpc.MarketServiceStub(self.channel)

    def search_item(self, name, category):
        try:
            for item in self.stub.SearchItem(shopping_platform_pb2.SearchItemRequest(name=name, category=category)):
                print(f"\nItem ID: {item.id}, Price: ${item.price}, Name: {item.name}, Category: {item.category}, "
                      f"Description: {item.description}.\nQuantity Remaining: {item.quantity}\nRating: {item.rating} / 5  |  "
                      f"Seller: {item.seller_address}\n")
        except grpc.RpcError as e:
            print(f"An error occurred during SearchItem: {e}")

    def buy_item(self, item_id, quantity, buyer_address):
        try:
            response = self.stub.BuyItem(shopping_platform_pb2.BuyItemRequest(
                item_id=item_id, quantity=quantity, buyer_address=buyer_address))
            print(f"Buy Item Response: {response.message}")
        except grpc.RpcError as e:
            print(f"An error occurred during BuyItem: {e}")

    def add_to_wishlist(self, item_id, buyer_address):
        try:
            response = self.stub.AddToWishlist(shopping_platform_pb2.WishlistRequest(
                item_id=item_id, buyer_address=buyer_address))
            print(f"Add To Wishlist Response: {response.message}")
        except grpc.RpcError as e:
            print(f"An error occurred during AddToWishlist: {e}")

    def rate_item(self, item_id, rating, buyer_address):
        try:
            response = self.stub.RateItem(shopping_platform_pb2.RateItemRequest(
                item_id=item_id, rating=rating, buyer_address=buyer_address))
            print(f"Rate Item Response: {response.message}")
        except grpc.RpcError as e:
            print(f"An error occurred during RateItem: {e}")

    # Function to simulate receiving notifications from the market
    def receive_notification(self, updated_item):
        # This would be a callback or part of a streaming RPC in a real-world scenario
        # For the assignment, we will print the notification to simulate this process
        print("#######\nThe Following Item has been updated:")
        print(f"Item ID: {updated_item.id}, Price: ${updated_item.price}, Name: {updated_item.name}, Category: {updated_item.category},\n"
              f"Description: {updated_item.description}.\nQuantity Remaining: {updated_item.quantity}\n"
              f"Rating: {updated_item.rating} / 5  |  Seller: {updated_item.seller_address}\n#######")

    def close(self):
        self.channel.close()

def menu():
    address = 'localhost:50051'
    buyer = BuyerClient(address)

    while True:
        print("\nMenu:")
        print("1. Search Item")
        print("2. Buy Item")
        print("3. Add Item to Wishlist")
        print("4. Rate Item")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            name = input("Enter item name: ")
            category = input("Enter item category: ").upper()
            buyer.search_item(name, category)

        elif choice == "2":
            item_id = int(input("Enter item ID: "))
            quantity = int(input("Enter quantity: "))
            buyer_address = input("Enter your address: ")
            buyer.buy_item(item_id, quantity, buyer_address)

        elif choice == "3":
            item_id = int(input("Enter item ID: "))
            buyer_address = input("Enter your address: ")
            buyer.add_to_wishlist(item_id, buyer_address)

        elif choice == "4":
            item_id = int(input("Enter item ID: "))
            rating = int(input("Enter your rating (1-5): "))
            buyer_address = input("Enter your address: ")
            buyer.rate_item(item_id, rating, buyer_address)

        elif choice == "5":
            break

        else:
            print("Invalid choice. Please try again.")

    buyer.close()

if __name__ == '__main__':
    menu()
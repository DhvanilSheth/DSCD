import grpc
import shopping_platform_pb2
import shopping_platform_pb2_grpc
import sys
import uuid
from concurrent import futures

# Notification service implementation for the buyer
class NotificationServiceServicer(shopping_platform_pb2_grpc.NotificationServiceServicer):
    def NotifyClient(self, request, context):
        print("\n#######\nNotification Received:")
        print(f"Message: {request.message}")
        if request.item.id:  # Checking if item details are included in the notification
            print(f"Item ID: {request.item.id}, Name: {request.item.name}, Price: {request.item.price}, "
                  f"Quantity: {request.item.quantity}, Rating: {request.item.rating} / 5")
        print("#######")
        return shopping_platform_pb2.Response(message="Notification received successfully.")

class BuyerClient:
    def __init__(self, address, notification_port):
        self.channel = grpc.insecure_channel(address)
        self.stub = shopping_platform_pb2_grpc.MarketServiceStub(self.channel)
        self.buyer_uuid = str(uuid.uuid1())
        self.notification_port = notification_port
        self.start_notification_server()

    def start_notification_server(self):
        # Start a server to listen for notifications
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        shopping_platform_pb2_grpc.add_NotificationServiceServicer_to_server(NotificationServiceServicer(), self.server)
        self.server.add_insecure_port(f'[::]:{self.notification_port}')
        self.server.start()
        print(f"Notification server started for buyer on port {self.notification_port}.")

    def register_buyer(self):
        request = shopping_platform_pb2.RegisterBuyerRequest(
            buyer_uuid=self.buyer_uuid,
            notification_endpoint=f'localhost:{self.notification_port}'
        )
        try:
            response = self.stub.RegisterBuyer(request)
            print(f"RegisterBuyer response: {response.message}")
        except grpc.RpcError as e:
            print(f"RegisterBuyer failed with {e.code()}: {e.details()}")

    def search_item(self, name, category):
        try:
            for item in self.stub.SearchItem(shopping_platform_pb2.SearchItemRequest(name=name, category=category, buyer_uuid = self.buyer_uuid)):
                print(f"\nItem ID: {item.id}, Price: ${item.price}, Name: {item.name}, Category: {shopping_platform_pb2.Category.Name(item.category)}, "
                      f"Description: {item.description}.\nQuantity Remaining: {item.quantity}\nRating: {item.rating} / 5  |  "
                      f"Seller: {item.seller_address}\n\n")
        except grpc.RpcError as e:
            print(f"An error occurred during SearchItem: {e}")

    def buy_item(self, item_id, quantity):
        try:
            response = self.stub.BuyItem(shopping_platform_pb2.BuyItemRequest(
                item_id=item_id, quantity=quantity, buyer_uuid=self.buyer_uuid))
            print(f"Buy Item Response: {response.message}")
        except grpc.RpcError as e:
            print(f"An error occurred during BuyItem: {e}")

    def add_to_wishlist(self, item_id):
        try:
            response = self.stub.AddToWishlist(shopping_platform_pb2.WishlistRequest(
                item_id=item_id, buyer_uuid=self.buyer_uuid))
            print(f"Add To Wishlist Response: {response.message}")
        except grpc.RpcError as e:
            print(f"An error occurred during AddToWishlist: {e}")

    def rate_item(self, item_id, rating):
        try:
            response = self.stub.RateItem(shopping_platform_pb2.RateItemRequest(
                item_id=item_id, rating=rating, buyer_uuid=self.buyer_uuid))
            print(f"Rate Item Response: {response.message}")
        except grpc.RpcError as e:
            print(f"An error occurred during RateItem: {e}")

    def close(self):
        self.server.stop(None)  # Properly stop the notification server
        self.channel.close()

def menu():
    server_address = sys.argv[1] if len(sys.argv) > 1 else 'localhost:50051'
    notification_port = sys.argv[2] if len(sys.argv) > 2 else '50052'
    buyer = BuyerClient(server_address, notification_port)
    print(f"UUID: {buyer.buyer_uuid}")
    print("Buyer client is running...")
    buyer.register_buyer()

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
            buyer.buy_item(item_id, quantity)

        elif choice == "3":
            item_id = int(input("Enter item ID: "))
            buyer.add_to_wishlist(item_id)

        elif choice == "4":
            item_id = int(input("Enter item ID: "))
            rating = int(input("Enter your rating (1-5): "))
            buyer.rate_item(item_id, rating)

        elif choice == "5":
            break

        else:
            print("Invalid choice. Please try again.")

    buyer.close()

if __name__ == '__main__':
    menu()
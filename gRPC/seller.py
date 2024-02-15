import grpc
import shopping_platform_pb2
import shopping_platform_pb2_grpc
import uuid
from concurrent import futures
import sys

# This class is for handling incoming notifications as a server
class NotificationServiceServicer(shopping_platform_pb2_grpc.NotificationServiceServicer):
    def NotifyClient(self, request, context):
        print("\n#######\nNotification Received:")
        print(f"Message: {request.message}")
        if request.item.id:  # Check if item details are included in the notification
            print(f"Item ID: {request.item.id}, Name: {request.item.name}, Price: {request.item.price}, "
                  f"Quantity: {request.item.quantity}, Rating: {request.item.rating} / 5")
        print("#######")
        return shopping_platform_pb2.Response(message="Notification received successfully.")


class SellerClient:
    def __init__(self, address, notification_port):
        self.seller_address = address
        self.notification_port = notification_port
        self.channel = grpc.insecure_channel(self.seller_address)
        self.stub = shopping_platform_pb2_grpc.MarketServiceStub(self.channel)
        self.uuid = str(uuid.uuid1())
        self.start_notification_server()

    def start_notification_server(self):
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        shopping_platform_pb2_grpc.add_NotificationServiceServicer_to_server(NotificationServiceServicer(), self.server)
        self.server.add_insecure_port(f'[::]:{self.notification_port}')
        self.server.start()
        print(f"Notification server started on port {self.notification_port}.")

    def register_seller(self):
        request = shopping_platform_pb2.RegisterSellerRequest(
            seller_address=self.seller_address,
            uuid=self.uuid,
            notification_endpoint=f'localhost:{self.notification_port}'  # Providing notification endpoint
        )
        try:
            response = self.stub.RegisterSeller(request)
            print(f"RegisterSeller response: {response.message}")
        except grpc.RpcError as e:
            print(f"RegisterSeller failed with {e.code()}: {e.details()}")

    def sell_item(self, name, category, quantity, description, price):
        request = shopping_platform_pb2.SellerItemOperationRequest(
            uuid=self.uuid,
            seller_address=self.seller_address,
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
            seller_address=self.seller_address,
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
            seller_address=self.seller_address,
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
    
    def close(self):
        self.server.stop(0)
        self.channel.close()

def menu():
    server_address = sys.argv[1] if len(sys.argv) > 1 else 'localhost:50051'
    notification_port = sys.argv[2] if len(sys.argv) > 2 else '50052'  # Default notification port
    seller = SellerClient(server_address, notification_port)
    print(f"UUID: {seller.uuid}")
    print("Seller client is running...")
    
    while True:
        print("\nMenu:")
        print("1. Register Seller")
        print("2. Sell Item")
        print("3. Update Item")
        print("4. Delete Item")
        print("5. Display Items")
        print("6. Exit")
        
        choice = input("Enter your choice: ")
        
        if choice == "1":
            seller.register_seller()

        elif choice == "2":
            name = input("Enter item name: ") 
            category = input("Enter item category: ")
            category = category.upper()
            quantity = int(input("Enter item quantity: "))
            description = input("Enter item description: ")
            price = float(input("Enter item price: "))
            seller.sell_item(name, category, quantity, description, price)
            
        elif choice == "3":
            item_id = int(input("Enter item ID: "))
            price = float(input("Enter new price: "))
            quantity = int(input("Enter new quantity: "))
            seller.update_item(item_id, price, quantity)
            
        elif choice == "4":
            item_id = int(input("Enter item ID: "))
            seller.delete_item(item_id)
            
        elif choice == "5":
            seller.display_items()
            
        elif choice == "6":
            break
            
        else:
            print("Invalid choice. Please try again.")
        
    seller.close()

if __name__ == '__main__':
    menu()

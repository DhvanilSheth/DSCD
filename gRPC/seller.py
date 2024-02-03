import grpc
import shopping_platform_pb2
import shopping_platform_pb2_grpc
import uuid
import sys
class SellerClient:
    
    def __init__(self, address):
        self.seller_address = address
        channel = grpc.insecure_channel(self.seller_address)
        self.stub = shopping_platform_pb2_grpc.MarketServiceStub(channel)
        self.uuid = str(uuid.uuid1())

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

def menu():
    server_address = sys.argv[1] if len(sys.argv) > 1 else 'localhost:50051'
    seller = SellerClient(server_address)
    print(f"UUID: {seller.uuid}")
    print("Seller client is running...")
    seller.register_seller()
    
    while True:
        print("\nMenu:")
        print("1. Sell Item")
        print("2. Update Item")
        print("3. Delete Item")
        print("4. Display Items")
        print("5. Exit")
        
        choice = input("Enter your choice: ")
        
        if choice == "1":
            name = input("Enter item name: ") 
            category = input("Enter item category: ")
            category = category.upper()
            quantity = int(input("Enter item quantity: "))
            description = input("Enter item description: ")
            price = float(input("Enter item price: "))
            seller.sell_item(name, category, quantity, description, price)
            
        elif choice == "2":
            item_id = int(input("Enter item ID: "))
            price = float(input("Enter new price: "))
            quantity = int(input("Enter new quantity: "))
            seller.update_item(item_id, price, quantity)
            
        elif choice == "3":
            item_id = int(input("Enter item ID: "))
            seller.delete_item(item_id)
            
        elif choice == "4":
            seller.display_items()
            
        elif choice == "5":
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    menu()

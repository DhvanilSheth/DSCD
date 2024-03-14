import grpc
from concurrent import futures
import time
import shopping_platform_pb2
import shopping_platform_pb2_grpc
import logging

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

class Market(shopping_platform_pb2_grpc.MarketServiceServicer):
    def __init__(self):
        self.sellers = {}  # {uuid: (seller_data, notification_endpoint)}
        self.buyers = {}  # {uuid: (buyer_data, notification_endpoint)}
        self.items = {}  # {item_id: item_data}
        self.wishlist = {}  # {item_id: [buyer_uuids]}
        self.ratings = {}  # {item_id: [ratings]}
        self.item_id_counter = 1

    def RegisterSeller(self, request, context):
        if request.uuid not in self.sellers:
            self.sellers[request.uuid] = (request, request.notification_endpoint)
            print(f"New seller registered: {request.seller_address}, uuid = {request.uuid}")
            return shopping_platform_pb2.Response(message="SUCCESS")
        else:
            return shopping_platform_pb2.Response(message="FAIL: Seller already registered")

    def SellItem(self, request, context):
        if request.uuid in self.sellers:
            new_item = shopping_platform_pb2.Item(
                id=self.item_id_counter,
                name=request.name,
                category=request.category,
                quantity=request.quantity,
                description=request.description,
                seller_address=request.seller_address,
                price=request.price,
                rating=0,  # Initial rating
                seller_uuid=request.uuid
            )
            self.items[self.item_id_counter] = new_item
            self.ratings[self.item_id_counter] = []  # Initialize the item's ratings list
            self.item_id_counter += 1
            print(f"New item added: {request.name} by {request.seller_address}")
            return shopping_platform_pb2.Response(message="SUCCESS")
        else:
            return shopping_platform_pb2.Response(message="FAIL: Seller not registered")

    def UpdateItem(self, request, context):
        if request.item_id in self.items and request.uuid == self.items[request.item_id].seller_uuid:
            item = self.items[request.item_id]
            item.price = request.price
            item.quantity = request.quantity
            self._notify_clients_about_item_update(request.item_id)
            print(f"Item updated: ID {request.item_id} by {request.seller_address}")
            return shopping_platform_pb2.Response(message="SUCCESS")
        else:
            return shopping_platform_pb2.Response(message="FAIL: Item not found or invalid credentials")


    def DeleteItem(self, request, context):
        if request.item_id in self.items and request.uuid == self.items[request.item_id].seller_uuid:
            del self.items[request.item_id]
            del self.ratings[request.item_id]
            print(f"Item deleted: ID {request.item_id}")
            return shopping_platform_pb2.Response(message="SUCCESS")
        else:
            return shopping_platform_pb2.Response(message="FAIL: Item not found or invalid credentials")

    def DisplaySellerItems(self, request, context):
        if request.uuid in self.sellers:
            for item in self.items.values():
                if item.seller_uuid == request.uuid:
                    print(f"Display request for Item ID: {item.id} from seller {request.uuid}")
                    yield item
        else:
            return shopping_platform_pb2.Response(message="FAIL: Seller not registered or invalid credentials")
        
    def RegisterBuyer(self, request, context):
        if request.buyer_uuid not in self.buyers:
            self.buyers[request.buyer_uuid] = (request, request.notification_endpoint)
            print(f"New buyer registered: uuid = {request.buyer_uuid}")
            return shopping_platform_pb2.Response(message="SUCCESS")
        else:
            return shopping_platform_pb2.Response(message="FAIL: Buyer already registered")

    # Implementing the SearchItem function
    def SearchItem(self, request, context):
        for item_id, item in self.items.items():
            if (request.category == item.category or request.category == shopping_platform_pb2.Category.ANY) and \
               (request.name.lower() in item.name.lower() or not request.name):
                yield item

    # Implementing the BuyItem function
    def BuyItem(self, request, context):
        if request.item_id in self.items and self.items[request.item_id].quantity >= request.quantity:
            self.items[request.item_id].quantity -= request.quantity
            self._notify_seller_about_purchase(request.item_id, request.quantity, request.buyer_uuid)
            print(f"Item bought: ID {request.item_id}, Quantity: {request.quantity}")
            return shopping_platform_pb2.Response(message="SUCCESS")
        else:
            return shopping_platform_pb2.Response(message="FAIL: Item not found or insufficient quantity")

    # Implementing the AddToWishlist function
    def AddToWishlist(self, request, context):
        if request.item_id in self.items:
            if request.item_id not in self.wishlist:
                self.wishlist[request.item_id] = []
            self.wishlist[request.item_id].append(request.buyer_uuid)
            print(f"Item wishlisted: ID {request.item_id} by Buyer UUID: {request.buyer_uuid}")
            return shopping_platform_pb2.Response(message="SUCCESS")
        else:
            return shopping_platform_pb2.Response(message="FAIL: Item not found")

    def RateItem(self, request, context):
        if request.item_id in self.items and 1 <= request.rating <= 5:
            # Add the rating to the item's list of ratings
            self.ratings.setdefault(request.item_id, []).append(request.rating)
            
            # Calculate the average rating
            avg_rating = sum(self.ratings[request.item_id]) / len(self.ratings[request.item_id])
            
            # Update the item's average rating
            self.items[request.item_id].rating = avg_rating
            
            print(f"Item rated: ID {request.item_id}, Rating: {request.rating}")
            return shopping_platform_pb2.Response(message="SUCCESS")
        else:
            return shopping_platform_pb2.Response(message="FAIL: Item not found or invalid rating")

    def _notify_clients_about_item_update(self, item_id):
        # Notify all buyers who have wish-listed the item about the update
        if item_id in self.wishlist:
            for buyer_uuid in self.wishlist[item_id]:
                buyer_data, notification_endpoint = self.buyers[buyer_uuid]
                self._send_notification(notification_endpoint, "Item has been updated.", item_id)

    def _notify_seller_about_purchase(self, item_id, quantity, buyer_uuid):
        # Notify the seller that their item has been purchased
        item = self.items[item_id]
        seller_data, notification_endpoint = self.sellers[item.seller_uuid]
        self._send_notification(notification_endpoint, f"Your item has been purchased. Quantity: {quantity}", item_id)

    def _send_notification(self, notification_endpoint, message, item_id):
        # Establish a gRPC client connection to the notification endpoint and send the notification
        channel = grpc.insecure_channel(notification_endpoint)
        stub = shopping_platform_pb2_grpc.NotificationServiceStub(channel)
        notification_message = shopping_platform_pb2.NotificationMessage(
            message=message,
            item=self.items.get(item_id, shopping_platform_pb2.Item())
        )
        response = stub.NotifyClient(notification_message)
        print(f"Notification sent: {response.message}")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    shopping_platform_pb2_grpc.add_MarketServiceServicer_to_server(Market(), server)
    server.add_insecure_port('0.0.0.0:50051')
    server.start()
    print("Market server started listening on port 50051.")
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)
        print("Market server stopped.")

if __name__ == '__main__':
    logging.basicConfig()
    serve()
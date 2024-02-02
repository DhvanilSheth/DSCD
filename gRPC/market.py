import grpc
from concurrent import futures
import time
import shopping_platform_pb2
import shopping_platform_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

class Market(shopping_platform_pb2_grpc.MarketServiceServicer):
    
    def __init__(self):
        self.sellers = {}  # {uuid: seller_address}
        self.items = {}  # {item_id: item}
        self.item_id_counter = 1
        self.wishlist = {}  # {item_id: [buyer_addresses]}
        self.item_ratings = {}  # {item_id: [ratings]}

    def RegisterSeller(self, request, context):
        if request.uuid in self.sellers:
            return shopping_platform_pb2.Response(message="FAIL")
        self.sellers[request.uuid] = request.seller_address
        print(f"Seller join request from {request.seller_address}, uuid = {request.uuid}")
        return shopping_platform_pb2.Response(message="SUCCESS")

    def SellItem(self, request, context):
        try:
            item = shopping_platform_pb2.Item(
                id=self.item_id_counter,
                name=request.name,
                category=request.category,
                quantity=request.quantity,
                description=request.description,
                seller_address=request.uuid, # address is taken as UUID 
                # seller_address=self.sellers[request.uuid],
                price=request.price,
                rating=0  # Default rating
            )
            self.items[self.item_id_counter] = item
            self.item_id_counter += 1
            print(f"Sell Item request from {self.sellers[request.uuid]}")
            return shopping_platform_pb2.Response(message="SUCCESS")
        except Exception as e:
            return shopping_platform_pb2.Response(message="FAIL")

    def UpdateItem(self, request, context):
        try: 
            if request.item_id not in self.items or request.uuid != self.items[request.item_id].seller_address:
                return shopping_platform_pb2.Response(message="FAIL")
            item = self.items[request.item_id]
            item.price = request.price
            item.quantity = request.quantity
            self._notify_clients_about_item_update(item)
            print(f"Update Item {request.item_id} request from {self.sellers[request.uuid]}")
            return shopping_platform_pb2.Response(message="SUCCESS")
        except Exception as e:
            return shopping_platform_pb2.Response(message="FAIL")

    def DeleteItem(self, request, context):
        try:
            if request.item_id in self.items and request.uuid == self.items[request.item_id].seller_address:
                del self.items[request.item_id]
                print(f"Delete Item {request.item_id} request from {self.sellers[request.uuid]}")
                return shopping_platform_pb2.Response(message="SUCCESS")
            return shopping_platform_pb2.Response(message="FAIL")
        except Exception as e:
            return shopping_platform_pb2.Response(message="FAIL")

    def DisplaySellerItems(self, request, context):
        try:
            seller_uuid = request.uuid
            for item in self.items.values():
                if item.seller_address == seller_uuid:
                    print(f"Display Items request from {self.sellers[request.uuid]}")
                    yield item
        except Exception as e:
            return shopping_platform_pb2.Response(message="FAIL")

    def SearchItem(self, request, context):
        for item in self.items.values():
            if (request.name in item.name or not request.name) and (item.category == request.category or request.category == shopping_platform_pb2.Category.ANY):
                print(f"Search request for Item name: {request.name}, Category: {item.category}")
                yield item

    def BuyItem(self, request, context):
        if request.item_id in self.items and self.items[request.item_id].quantity >= request.quantity:
            item = self.items[request.item_id]
            item.quantity -= request.quantity
            print(f"Buy request {request.quantity} of item {request.item_id}, from {request.buyer_address}")
            self._notify_seller_about_purchase(item, request.quantity, request.buyer_address)
            return shopping_platform_pb2.Response(message="SUCCESS")
        return shopping_platform_pb2.Response(message="FAIL")

    def AddToWishlist(self, request, context):
        if request.item_id in self.items:
            if request.item_id not in self.wishlist:
                self.wishlist[request.item_id] = []
            self.wishlist[request.item_id].append(request.buyer_address)
            print(f"Wishlist request of item {request.item_id}, from {request.buyer_address}")
            return shopping_platform_pb2.Response(message="SUCCESS")
        return shopping_platform_pb2.Response(message="FAIL")

    def RateItem(self, request, context):
        if request.item_id in self.items and 1 <= request.rating <= 5:
            self.item_ratings.setdefault(request.item_id, []).append(request.rating)
            avg_rating = sum(self.item_ratings[request.item_id]) / len(self.item_ratings[request.item_id])
            self.items[request.item_id].rating = avg_rating
            print(f"{request.buyer_address} rated item {request.item_id} with {request.rating} stars.")
            return shopping_platform_pb2.Response(message="SUCCESS")
        return shopping_platform_pb2.Response(message="FAIL")

    def _notify_clients_about_item_update(self, updated_item):
        if updated_item.id in self.wishlist:
            for buyer_address in self.wishlist[updated_item.id]:
                # In a real implementation, you'd establish a connection to the buyer and send the notification
                # For this assignment, we'll just print a message to simulate this
                print(f"Notification for {buyer_address}: The item {updated_item.name} has been updated.")

    def _notify_seller_about_purchase(self, item, quantity, buyer_address):
        # In a real implementation, you'd establish a connection to the seller and send the notification
        # For this assignment, we'll just print a message to simulate this
        seller_address = item.seller_address
        print(f"Notification for seller at {seller_address}: {quantity} units of item {item.name} have been purchased by {buyer_address}.")

    def NotifyClient(self, request, context):
        # This method should be implemented based on the actual notification logic.
        # Here we'll just print out the notification details to simulate the notification process.
        print("#######\nThe Following Item has been updated:")
        print(f"Item ID: {request.item.id}, Price: ${request.item.price}, Name: {request.item.name}, "
              f"Category: {request.item.category},\nDescription: {request.item.description}.")
        print(f"Quantity Remaining: {request.item.quantity}\nRating: {request.item.rating} / 5  |  "
              f"Seller: {request.item.seller_address}\n#######")
        return shopping_platform_pb2.Response(message="NOTIFICATION_SENT")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    shopping_platform_pb2_grpc.add_MarketServiceServicer_to_server(Market(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Market server started on port 50051.")
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)
        print("Market server stopped.")

if __name__ == '__main__':
    serve()
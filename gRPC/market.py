from concurrent import futures
import grpc
import shopping_platform_pb2
import shopping_platform_pb2_grpc

class MarketService(shopping_platform_pb2_grpc.MarketServiceServicer):
    def __init__(self):
        self.sellers = {}  # Dictionary to store seller info
        self.items = {}  # Dictionary to store item info
        self.item_id_counter = 1  # Counter to assign unique IDs to items
        self.wishlists = {}  # Dictionary to store buyers' wishlists

    def RegisterSeller(self, request, context):
        if request.uuid in self.sellers:
            return shopping_platform_pb2.Response(message="FAIL: Seller already registered.")
        self.sellers[request.uuid] = request.address
        return shopping_platform_pb2.Response(message="SUCCESS")

    def SellItem(self, request, context):
        item = request.item
        item.id = self.item_id_counter
        self.items[self.item_id_counter] = item
        self.item_id_counter += 1
        return shopping_platform_pb2.Response(message=f"SUCCESS: Item ID {item.id}")

    def UpdateItem(self, request, context):
        item_id = request.item.id
        if item_id in self.items:
            self.items[item_id] = request.item
            # Notify buyers in the wishlist
            for buyer in self.wishlists.get(item_id, []):
                self._notify_client(buyer, item_id)
            return shopping_platform_pb2.Response(message="SUCCESS")
        return shopping_platform_pb2.Response(message="FAIL: Item not found.")

    def DeleteItem(self, request, context):
        item_id = request.item.id
        if item_id in self.items:
            del self.items[item_id]
            return shopping_platform_pb2.Response(message="SUCCESS")
        return shopping_platform_pb2.Response(message="FAIL: Item not found.")

    def DisplaySellerItems(self, request, context):
        for item_id, item in self.items.items():
            if item.seller_address == request.address:
                yield item

    def SearchItem(self, request, context):
        for item_id, item in self.items.items():
            if (request.name in item.name or not request.name) and \
               (item.category == request.category or request.category == shopping_platform_pb2.ANY):
                yield item

    def BuyItem(self, request, context):
        item_id = request.item_id
        quantity = request.quantity
        if item_id in self.items and self.items[item_id].quantity >= quantity:
            self.items[item_id].quantity -= quantity
            return shopping_platform_pb2.Response(message="SUCCESS")
        return shopping_platform_pb2.Response(message="FAIL: Item not available or insufficient quantity.")

    def AddToWishlist(self, request, context):
        if request.item_id not in self.wishlists:
            self.wishlists[request.item_id] = []
        self.wishlists[request.item_id].append(request.buyer_address)
        return shopping_platform_pb2.Response(message="SUCCESS")

    def RateItem(self, request, context):
        # Simplified rating logic: updating rating without considering previous ratings
        if request.item_id in self.items:
            self.items[request.item_id].rating = request.rating
            return shopping_platform_pb2.Response(message="SUCCESS")
        return shopping_platform_pb2.Response(message="FAIL: Item not found.")

    def NotifyClient(self, request_iterator, context):
        # This method is a placeholder for the notification mechanism
        pass

    def _notify_client(self, buyer_address, item_id):
        # Placeholder method for sending notifications to buyers
        pass

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    shopping_platform_pb2_grpc.add_MarketServiceServicer_to_server(MarketService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()

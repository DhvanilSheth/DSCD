import time
from concurrent import futures

import grpc
import shopping_pb2
import shopping_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

# This is a simple in-memory structure to store sellers and items.
# In a real-world application, you would interface with a database.
sellers = {}
items = {}
item_id_counter = 1


class MarketServicer(shopping_pb2_grpc.MarketServicer):

    def RegisterSeller(self, request, context):
        global sellers
        if request.address in sellers:
            return shopping_pb2.SellerActionResponse(message="FAIL")
        sellers[request.address] = request.uuid
        print(f"Seller join request from {request.address}, uuid = {request.uuid}")
        return shopping_pb2.SellerActionResponse(message="SUCCESS")

    def SellItem(self, request, context):
        global item_id_counter
        global items
        item = request
        item.id = item_id_counter
        item_id_counter += 1
        items[item.id] = item
        print(f"Sell Item request from {item.seller_address}")
        return shopping_pb2.SellerActionResponse(message="SUCCESS", item_id=item.id)

    # Add other service methods here like UpdateItem, DeleteItem, etc.

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    shopping_pb2_grpc.add_MarketServicer_to_server(MarketServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Market server started on port 50051.")
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()

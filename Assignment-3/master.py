import grpc
from concurrent import futures
import time
import random
import kmeans_pb2
import kmeans_pb2_grpc

class MasterServer:
    def __init__(self, mappers, reducers, centroids, iterations, input_file):
        self.num_mappers = mappers
        self.num_reducers = reducers
        self.num_centroids = centroids
        self.max_iterations = iterations
        self.input_file = input_file

    def start_map_reduce(self):
        # Method to start the MapReduce process for K-Means clustering.
        # This includes the iterative process, invoking mappers and reducers,
        # handling failures, and updating centroids.

        # Pseudocode for starting the iterative process:
        for iteration in range(self.max_iterations):
            print(f"Starting iteration {iteration+1}")

            # Perform the mapping tasks
            self.start_mapping()

            # Perform the reducing tasks
            self.start_reducing()

            # Check for convergence or update centroids
            # If converged, break the loop

            # Logging the centroids and iteration info
            print(f"Centroids after iteration {iteration+1}: {self.centroids}")

    def start_mapping(self):
        chunk_size = len(self.input_file) // self.num_mappers
        remaining_data = len(self.input_file) % self.num_mappers

        for mapper_id in range(self.num_mappers):
            start_index = mapper_id * chunk_size
            end_index = start_index + chunk_size

            if mapper_id == self.num_mappers - 1:
                end_index += remaining_data

            data_chunk = self.input_file[start_index:end_index]

            with grpc.insecure_channel(f'localhost:{50051+mapper_id}') as channel:
                stub = kmeans_pb2_grpc.KMeansServiceStub(channel)
                centroids = [kmeans_pb2.Point(id=i, coordinates=c) for i, c in enumerate(self.centroids)]
                response = stub.MapTask(kmeans_pb2.MapperRequest(mapper_id=mapper_id, input_data=data_chunk, centroids=centroids))
                print(f"Mapper {mapper_id} response: {response.success}")

    def start_reducing(self):
        for reducer_id in range(self.num_reducers):
            keys = []  # Collect keys from mappers
            for mapper_id in range(self.num_mappers):
                with open(f"Mappers/M{mapper_id}/partition_{reducer_id}.txt", "r") as file:
                    keys.extend(map(int, file.read().splitlines()))

            with grpc.insecure_channel(f'localhost:{60051+reducer_id}') as channel:
                stub = kmeans_pb2_grpc.KMeansServiceStub(channel)
                response = stub.ReduceTask(kmeans_pb2.ReducerRequest(reducer_id=reducer_id, keys=keys))
                print(f"Reducer {reducer_id} response: {response.success}")

    def check_mapper_failure(self, mapper_id):
        # Implemention of fault tolerance by checking if a mapper has failed.
        # If so, restart the mapper task.
        pass

    def check_reducer_failure(self, reducer_id):
        # Similar to check_mapper_failure, but for reducers.
        pass

# Function to serve the Master server using gRPC
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kmeans_pb2_grpc.add_MasterServicer_to_server(MasterServer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    m, r, c, i = int(input("Enter number of mappers: ")), int(input("Enter number of reducers: ")), int(input("Enter number of centroids: ")), int(input("Enter number of iterations: "))
    master = MasterServer(m, r, c, i, "points.txt")
    master.start_map_reduce()
    serve()

import grpc
import kmeans_pb2
import kmeans_pb2_grpc
import random
import time
import subprocess
import os
import sys
from concurrent import futures

class Master(kmeans_pb2_grpc.KMeansServiceServicer):
    def __init__(self, mappers, reducers, centroids, iterations, input_file):
        self.num_mappers = mappers
        self.num_reducers = reducers
        self.num_centroids = centroids
        self.max_iterations = iterations
        self.input_file = input_file
        self.data = self.load_input_file(input_file)
        self.centroids = self.initialize_centroids(centroids, self.data)

    def initialize_centroids(self, num_centroids, data):
        centroids = random.sample(data, num_centroids)
        with open("centroids.txt", "w") as file:
            for centroid in centroids:
                file.write(f"{centroid}\n")
        return centroids

    def load_input_file(self, input_file):
        with open(input_file, "r") as file:
            data = [line.strip() for line in file]
        return data

    def start_map_reduce(self):
        for iteration in range(self.max_iterations):
            print(f"Starting iteration {iteration+1}")

            self.start_mapping()

            self.start_reducing()

            self.update_centroids()

            print(f"Centroids after iteration {iteration+1}: {self.centroids}")

    def start_mapping(self):
        chunk_size = len(self.data) // self.num_mappers
        remaining_data = len(self.data) % self.num_mappers

        for mapper_id in range(self.num_mappers):
            start_index = mapper_id * chunk_size
            end_index = start_index + chunk_size

            if mapper_id == self.num_mappers - 1:
                end_index += remaining_data

            data_chunk = self.data[start_index:end_index]

            with grpc.insecure_channel(f'localhost:{50051+mapper_id}') as channel:
                stub = kmeans_pb2_grpc.KMeansServiceStub(channel)
                centroids = [kmeans_pb2.Point(id=i, coordinates=c) for i, c in enumerate(self.centroids)]
                try:
                    response = stub.MapTask(kmeans_pb2.MapperRequest(mapper_id=mapper_id, input_data=data_chunk, centroids=centroids))
                    if not response.success:
                        print(f"Mapper {mapper_id} failed")
                        self.retry_mapping(mapper_id, data_chunk, centroids)
                except grpc.RpcError as e:
                    print(f"Mapper {mapper_id} failed with error: {e}")
                    self.retry_mapping(mapper_id, data_chunk, centroids)
            
    def retry_mapping(self, mapper_id, data_chunk, centroids):
        with grpc.insecure_channel(f'localhost:{50051+mapper_id}') as channel:
            stub = kmeans_pb2_grpc.KMeansServiceStub(channel)
            response = stub.MapTask(kmeans_pb2.MapperRequest(mapper_id=mapper_id, input_data=data_chunk, centroids=centroids))
            print(f"Mapper {mapper_id} response: {response.success}")
            
    def start_reducing(self):
        for reducer_id in range(self.num_reducers):
            keys = []  
            for mapper_id in range(self.num_mappers):
                with open(f"Mappers/M{mapper_id}/partition_{reducer_id}.txt", "r") as file:
                    keys.extend(map(int, file.read().splitlines()))

            with grpc.insecure_channel(f'localhost:{60051+reducer_id}') as channel:
                stub = kmeans_pb2_grpc.KMeansServiceStub(channel)
                try:
                    response = stub.ReduceTask(kmeans_pb2.ReducerRequest(reducer_id=reducer_id, keys=keys))
                    if not response.success:
                        print(f"Reducer {reducer_id} failed")
                        self.retry_reducing(reducer_id, keys)
                except grpc.RpcError as e:
                    print(f"Reducer {reducer_id} failed with error: {e}")
                    self.retry_reducing(reducer_id, keys)
    
    def retry_reducing(self, reducer_id, keys):
        with grpc.insecure_channel(f'localhost:{60051+reducer_id}') as channel:
            stub = kmeans_pb2_grpc.KMeansServiceStub(channel)
            response = stub.ReduceTask(kmeans_pb2.ReducerRequest(reducer_id=reducer_id, keys=keys))
            print(f"Reducer {reducer_id} response: {response.success}")

    def update_centroids(self):
        centroids = []
        for reducer_id in range(self.num_reducers):
            with open(f"Reducers/R{reducer_id}.txt", "r") as file:
                centroids.extend([line.strip() for line in file])
        self.centroids = centroids
        with open("centroids.txt", "w") as file:
            for centroid in centroids:
                file.write(f"{centroid}\n")

    def MapperResponse(self, request, context):
        print(f"Received response from Mapper {request.mapper_id}: {request.success}")
        return kmeans_pb2.Empty()

    def ReducerResponse(self, request, context):
        print(f"Received response from Reducer {request.reducer_id}: {request.success}")
        return kmeans_pb2.Empty()

def serve(master):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kmeans_pb2_grpc.add_KMeansServiceServicer_to_server(master, server)
    server.add_insecure_port('[::]:40051')
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    if len(sys.argv) != 6:
        print("Usage: master.py <num_mappers> <num_reducers> <num_centroids> <max_iterations> <input_file>")
        sys.exit(1)

    num_mappers = int(sys.argv[1])
    num_reducers = int(sys.argv[2])
    num_centroids = int(sys.argv[3])
    max_iterations = int(sys.argv[4])
    input_file = sys.argv[5]

    master = Master(num_mappers, num_reducers, num_centroids, max_iterations, input_file)
    master.start_map_reduce()
    serve(master)
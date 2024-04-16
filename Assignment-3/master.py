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
        self.mapper_processes = []
        self.reducer_processes = []

    def initialize_centroids(self, num_centroids, data):
        centroids = random.sample(data, num_centroids)
        with open("Data/centroids.txt", "w") as file:
            for i, centroid in enumerate (centroids):
                file.write(f"{','.join(map(str, centroid))}\n")
                print(f"Initialized Centroid {i} : {centroid}")
        return centroids

    def load_input_file(self, input_file):
        with open(input_file, "r") as file:
            data = [[float(num) for num in line.strip().split(",")] for line in file]
            print(f"Data: {data}")
        return data
    
    def start_map_reduce(self):
        for iteration in range(self.max_iterations):
            print(f"Starting iteration {iteration+1}")

            self.start_mapping()
            print(f"Mapping completed")

            self.start_reducing()
            print(f"Reducing completed")

            self.update_centroids()
            print(f"Centroids updated")

            print(f"Centroids after iteration {iteration+1}: {self.centroids}")

    def start_mapping(self):
        chunk_size = len(self.data) // self.num_mappers
        remaining_data = len(self.data) % self.num_mappers

        for mapper_id in range(self.num_mappers):
            start_index = mapper_id * chunk_size
            end_index = start_index + chunk_size

            if mapper_id == self.num_mappers - 1:
                end_index += remaining_data

            print(f"Mapper {mapper_id} processing data from index {start_index} to {end_index}")
            process = subprocess.Popen(['python', 'mapper.py', str(self.num_reducers), str(50051 + mapper_id)])
            self.mapper_processes.append(process)

            with grpc.insecure_channel(f'localhost:{50051+mapper_id}') as channel:
                stub = kmeans_pb2_grpc.KMeansServiceStub(channel)
                centroids = [kmeans_pb2.Point(id=i, x_coordinate=[c[0]], y_coordinate=[c[1]]) for i, c in enumerate(self.centroids)]
                for attempt in range(4):
                    try:
                        response = stub.MapTask(kmeans_pb2.MapperRequest(mapper_id = mapper_id, start_idx = start_index, end_idx = end_index, centroids = centroids))
                        if response.success:
                            print(f"Mapper {mapper_id} response: {response.success}")
                            break
                    except grpc.RpcError as e:
                        print(f"Mapper {mapper_id} failed with error: {e} , retring attempt {attempt}")
                        time.sleep(2)

    def start_reducing(self):
        for reducer_id in range(self.num_reducers):
            keys = []
            x_coordinates = []
            y_coordinates = []
            for mapper_id in range(self.num_mappers):
                with open(f"Data/Mappers/M{mapper_id}/partition_{reducer_id}.txt", "r") as file:
                    for line in file:
                        key, x, y = map(float, line.split())
                        keys.append(int(key))
                        x_coordinates.append(x)
                        y_coordinates.append(y)

            data_points = [kmeans_pb2.Point(id=int(key), x_coordinate=[x], y_coordinate=[y]) for key, x, y in zip(keys, x_coordinates, y_coordinates)]
            centroids = [kmeans_pb2.Point(id=i, x_coordinate=[c[0]], y_coordinate=[c[1]]) for i, c in enumerate(self.centroids)]
            print(f"Reducer {reducer_id} processing data: {data_points}")

            process = subprocess.Popen(['python', 'reducer.py', str(reducer_id), str(60051 + reducer_id)])
            self.reducer_processes.append(process)

            with grpc.insecure_channel(f'localhost:{60051+reducer_id}') as channel:
                stub = kmeans_pb2_grpc.KMeansServiceStub(channel)
                for attempt in range(4):
                    try:
                        response = stub.ReduceTask(kmeans_pb2.ReducerRequest(reducer_id=reducer_id, keys=list(map(int, keys)), centroids=centroids, data_points=data_points))
                        if response.success:
                            print(f"Reducer {reducer_id} response: {response.success}")
                            break
                    except grpc.RpcError as e:
                        print(f"Reducer {reducer_id} failed with error: {e} , retring attempt {attempt}")
                        time.sleep(2)

    def update_centroids(self):
        centroids = []
        for reducer_id in range(self.num_reducers):
            with open(f"Data/Reducers/R{reducer_id}.txt", "r") as file:
                for line in file:
                    centroid = list(map(float, line.split()[1:]))
                    centroids.append(centroid)
        self.centroids = centroids
        with open("Data/centroids.txt", "w") as file:
            for centroid in centroids:
                file.write(f"{','.join(map(str, centroid))}\n")

    def MapperResponse(self, request, context):
        print(f"Received response from Mapper {request.mapper_id}: {request.success}")
        return kmeans_pb2.Empty()

    def ReducerResponse(self, request, context):
        print(f"Received response from Reducer {request.reducer_id}: {request.success}")
        return kmeans_pb2.Empty()

    def terminate_processes(self):
        print("Terminating processes")
        for process in self.mapper_processes:
            process.terminate()
        for process in self.reducer_processes:
            process.terminate()

def serve(master):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kmeans_pb2_grpc.add_KMeansServiceServicer_to_server(master, server)
    server.add_insecure_port('localhost:40051')
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("Usage: master.py <num_mappers> <num_reducers> <num_centroids> <max_iterations> <input_file>")
        sys.exit(1)

    num_mappers = int(sys.argv[1])
    num_reducers = int(sys.argv[2])
    num_centroids = int(sys.argv[3])
    max_iterations = int(sys.argv[4])
    input_file = "Data/Input/points.txt"

    master = Master(num_mappers, num_reducers, num_centroids, max_iterations, input_file)
    master.start_map_reduce()
    serve(master)
    master.terminate_processes()
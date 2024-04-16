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
            print("Mapping completed")

            self.start_reducing()
            print("Reducing completed")

            self.update_centroids()

            print(f"Centroids after iteration {iteration+1}: {self.centroids}")
    
    def start_mapping(self):
        chunk_size = len(self.data) // self.num_mappers
        remaining_data = len(self.data) % self.num_mappers

        for mapper_id in range(self.num_mappers):
            start_index = mapper_id * chunk_size
            end_index = start_index + chunk_size + (remaining_data if mapper_id == self.num_mappers - 1 else 0)

            print(f"Mapper {mapper_id} processing data from index {start_index} to {end_index}")
            process = subprocess.Popen(['python', 'mapper.py', str(self.num_reducers), str(80051 + mapper_id)])
            self.mapper_processes.append(process)

            success = self.attempt_rpc(mapper_id, start_index, end_index, 'map')
            if not success:
                print(f"Failed to complete mapping task with Mapper {mapper_id} after several attempts.")

    def attempt_rpc(self, service_id, start_idx, end_idx, task_type, attempts=3, delay=2):
        for attempt in range(attempts):
            try:
                with grpc.insecure_channel(f'localhost:{80051+service_id}') as channel:
                    stub = kmeans_pb2_grpc.KMeansServiceStub(channel)
                    centroids = [kmeans_pb2.Point(id=i, x_coordinate=[c[0]], y_coordinate=[c[1]]) for i, c in enumerate(self.centroids)]
                    if task_type == 'map':
                        response = stub.MapTask(kmeans_pb2.MapperRequest(mapper_id=service_id, start_idx=start_idx, end_idx=end_idx, centroids=centroids))
                    elif task_type == 'reduce':
                        response = stub.ReduceTask(kmeans_pb2.ReducerRequest(reducer_id=service_id, keys=start_idx))
                    if response.success:
                        return True
            except grpc.RpcError as e:
                print(f"Attempt {attempt+1} failed for {task_type} task with service ID {service_id}: {e}")
            time.sleep(delay)
        return False

    def start_reducing(self):
        for reducer_id in range(self.num_reducers):
            keys = set()
            for mapper_id in range(self.num_mappers):
                with open(f"Data/Mappers/M{mapper_id}/partition_{reducer_id}.txt", "r") as file:
                    keys.update([int(line.strip().split("\t")[0]) for line in file])

            print(f"Reducer {reducer_id} processing keys: {keys}")
            process = subprocess.Popen(['python', 'reducer.py', str(reducer_id), str(60051 + reducer_id)])
            self.reducer_processes.append(process)

            success = self.attempt_rpc(reducer_id, list(keys), None, 'reduce')
            if not success:
                print(f"Failed to complete reducing task with Reducer {reducer_id} after several attempts.")

    def update_centroids(self):
        centroids = []
        for reducer_id in range(self.num_reducers):
            with open(f"Data/Reducers/R{reducer_id}.txt", "r") as file:
                centroids.extend([list(map(float, line.strip().split(","))) for line in file])
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
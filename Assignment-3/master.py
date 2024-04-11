import grpc
from concurrent import futures
import time
import subprocess
import os
import random
import kmeans_pb2
import kmeans_pb2_grpc

class MasterServer:
    def __init__(self, mappers, reducers, centroids, iterations, input_file):
        self.num_mappers = mappers
        self.num_reducers = reducers
        self.centroids = self.initialize_centroids(centroids, input_file)
        self.max_iterations = iterations
        self.input_file = self.load_input_file(input_file)

    def initialize_centroids(self, num_centroids, input_file):
        # Load the input data and select `num_centroids` random points
        data = self.load_input_file(input_file)
        centroids = random.sample(data, num_centroids)
        # Write the initial centroids to a file
        with open("centroids.txt", "w") as file:
            for centroid in centroids:
                file.write(f"{centroid}\n")
        return centroids

    def load_input_file(self, input_file):
        # Load the input data from a file
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
        for mapper_id in range(self.num_mappers):
            command = ["python", "mapper.py", str(mapper_id), str(self.num_centroids)]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                print(f"Mapper {mapper_id} failed with error: {stderr.decode()}")
            else:
                print(f"Mapper {mapper_id} completed successfully")

    def start_reducing(self):
        for reducer_id in range(self.num_reducers):
            command = ["python", "reducer.py", str(reducer_id)]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                print(f"Reducer {reducer_id} failed with error: {stderr.decode()}")
            else:
                print(f"Reducer {reducer_id} completed successfully")

    def update_centroids(self):
        # Load the output of the reducers and update the centroids
        centroids = []
        for reducer_id in range(self.num_reducers):
            with open(f"Reducers/R{reducer_id}.txt", "r") as file:
                centroids.extend([line.strip() for line in file])
        self.centroids = centroids
        # Write the updated centroids to a file
        with open("centroids.txt", "w") as file:
            for centroid in centroids:
                file.write(f"{centroid}\n")

    def check_mapper_failure(self, mapper_id):
        if not os.path.exists(f"Mappers/M{mapper_id}/keys.txt"):
            print(f"Mapper {mapper_id} has failed. Restarting...")
            self.start_mapping_for_mapper(mapper_id)

    def check_reducer_failure(self, reducer_id):
        if not os.path.exists(f"Reducers/R{reducer_id}.txt"):
            print(f"Reducer {reducer_id} has failed. Restarting...")
            self.start_reducing_for_reducer(reducer_id)

    def start_mapping_for_mapper(self, mapper_id):
        # Start the mapping task for a specific mapper
        # This is similar to the start_mapping method, but only for one mapper
        pass

    def start_reducing_for_reducer(self, reducer_id):
        # Start the reducing task for a specific reducer
        # This is similar to the start_reducing method, but only for one reducer
        pass

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
import grpc
from concurrent import futures
import kmeans_pb2
import kmeans_pb2_grpc
import os
import sys

class Mapper(kmeans_pb2_grpc.KMeansServiceServicer):
    def __init__(self, num_reducers, input_file):
        self.centroids = []
        self.num_reducers = num_reducers
        self.input_file = input_file

    def MapTask(self, request, context):
        mapper_id = request.mapper_id
        start_idx = request.start_idx
        end_idx = request.end_idx

        centroids = self._parse_centroids(request.centroids)
        print(f"Mapper {mapper_id}, received Centroids : {centroids} ")
        data_points = self._read_data_points(start_idx, end_idx)
        print(f"Mapper {mapper_id}, Data Points : {data_points} ")
        mapped_data = self._map_data(data_points, centroids)
        print(f"Mapper {mapper_id}, Mapped Data : {mapped_data} ")
        self._write_to_file(mapped_data, mapper_id)
        partitions = self._partition_data(mapped_data)
        print(f"Mapper {mapper_id}, Partitions : {partitions} ")
        self._write_partitions(partitions, mapper_id)

        return kmeans_pb2.MapperResponse(
            mapper_id=mapper_id,
            success=True,
            message="Mapping and partitioning completed successfully."
        )

    def _parse_centroids(self, centroids):
        parsed_centroids = [[point.x_coordinate[0], point.y_coordinate[0]] for point in centroids]
        print(f"Parsed Centroids : {parsed_centroids} ")
        return parsed_centroids

    def _read_data_points(self, start_idx, end_idx):
        with open(self.input_file, 'r') as f:
            lines = f.readlines()[start_idx:end_idx]
        data_points = [list(map(float, line.strip().split(","))) for line in lines]
        return data_points

    def _map_data(self, data_points, centroids):
        mapped_data = []
        for point in data_points:
            nearest_centroid_index = self._find_nearest_centroid(point, centroids)
            mapped_data.append((nearest_centroid_index, point))
        return mapped_data

    def _find_nearest_centroid(self, point, centroids):
        min_distance = float('inf')
        nearest_centroid_index = -1
        for i, centroid in enumerate(centroids):
            distance = self._calculate_distance(point, centroid)
            if distance < min_distance:
                min_distance = distance
                nearest_centroid_index = i
        print(f"Nearest Centroid for point {point} : {nearest_centroid_index} ")
        return nearest_centroid_index

    def _calculate_distance(self, point, centroid):
        distance = sum((a - b) ** 2 for a, b in zip(point, centroid)) ** 0.5
        print(f"Calculated Distance between {point} and {centroid} : {distance} ")
        return distance

    def _write_to_file(self, mapped_data, mapper_id):
        os.makedirs(f'Data/Mappers/M{mapper_id}', exist_ok=True)
        with open(f'Data/Mappers/M{mapper_id}/mapper_{mapper_id}_output.txt', 'w') as f:
            for key, point in mapped_data:
                f.write(f"{key}\t{' '.join(map(str, point))}\n")
        print(f"Wrote Mapped Data to File for Mapper {mapper_id} to mapper_{mapper_id}_output.txt ")

    def _partition_data(self, mapped_data):
        partitions = {i: [] for i in range(self.num_reducers)}
        for key, point in mapped_data:
            partition_id = key % self.num_reducers
            partitions[partition_id].append((key, point))
        print(f"Partitioned Data : {partitions} ")
        return partitions
    
    def _write_partitions(self, partitions, mapper_id):
        os.makedirs(f'Data/Mappers/M{mapper_id}', exist_ok=True)
        for partition_id, partition in partitions.items():
            partition_file_path = f'Data/Mappers/M{mapper_id}/partition_{partition_id}.txt'
            with open(partition_file_path, 'w') as f:
                for key, point in partition:
                    f.write(f"{key}\t{' '.join(map(str, point))}\n")
            print(f"Wrote Partition {partition_id} to File for Mapper {mapper_id} ")

def serve_mapper(num_reducers, port, input_file):
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        kmeans_pb2_grpc.add_KMeansServiceServicer_to_server(Mapper(num_reducers, input_file), server)
        server.add_insecure_port(f'localhost:{port}')
        server.start()
        server.wait_for_termination()
    except RuntimeError:
        pass

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: mapper.py <num_reducers> <port> <input_file>")
        sys.exit(1)

    num_reducers = int(sys.argv[1])
    port = int(sys.argv[2])
    input_file = sys.argv[3]
    serve_mapper(num_reducers, port, input_file)
import grpc
from concurrent import futures
import kmeans_pb2
import kmeans_pb2_grpc
import json
import os
import sys

class Mapper(kmeans_pb2_grpc.KMeansServiceServicer):
    def __init__(self, num_reducers):
        self.centroids = []
        self.num_reducers = num_reducers

    def MapTask(self, request, context):
        mapper_id = request.mapper_id
        start_idx = request.start_idx
        end_idx = request.end_idx
        centroids = self._parse_centroids(request.centroids)

        data_points = self._read_data_points(start_idx, end_idx)
        mapped_data = self._map_data(data_points, centroids)
        self._write_to_file(mapped_data, mapper_id)
        partitions = self._partition_data(mapped_data)
        self._write_partitions(partitions, mapper_id)

        return kmeans_pb2.MapperResponse(
            mapper_id=mapper_id,
            success=True,
            message="Mapping and partitioning completed successfully."
        )

    def _parse_centroids(self, centroids):
        return [point.coordinates for point in centroids]

    def _read_data_points(self, start_idx, end_idx):
        with open('Data/Input/points.txt', 'r') as f:
            lines = f.readlines()[start_idx:end_idx]
        return [list(map(float, line.strip().split(","))) for line in lines]

    def _map_data(self, data_points, centroids):
        mapped_data = {}
        for point in data_points:
            nearest_centroid_index = self._find_nearest_centroid(point, centroids)
            if nearest_centroid_index not in mapped_data:
                mapped_data[nearest_centroid_index] = []
            mapped_data[nearest_centroid_index].append(point)
        return mapped_data

    def _find_nearest_centroid(self, point, centroids):
        min_distance = float('inf')
        nearest_centroid_index = -1
        for i, centroid in enumerate(centroids):
            distance = self._calculate_distance(point, centroid)
            if distance < min_distance:
                min_distance = distance
                nearest_centroid_index = i
        return nearest_centroid_index

    def _calculate_distance(self, point, centroid):
        return sum((a - b) ** 2 for a, b in zip(point, centroid)) ** 0.5

    def _write_to_file(self, mapped_data, mapper_id):
        os.makedirs(f'Data/Mappers/M{mapper_id}', exist_ok=True)
        for key, points in mapped_data.items():
            with open(f'Data/Mappers/M{mapper_id}/mapper_{mapper_id}_output.txt', 'w') as f:
                for point in points:
                    f.write(' '.join(map(str, point)) + '\n')

    def _partition_data(self, mapped_data):
        partitions = {i: {} for i in range(self.num_reducers)}
        for key, points in mapped_data.items():
            partition_id = key % self.num_reducers
            partitions[partition_id][key] = points
        return partitions

    def _write_partitions(self, partitions, mapper_id):
        for partition_id, partition in partitions.items():
            with open(f'Data/Mappers/M{mapper_id}/partition_{partition_id}.txt', 'w') as f:
                for key, points in partition.items():
                    for point in points:
                        f.write(' '.join(map(str, point)) + '\n')

def serve_mapper(num_reducers, port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kmeans_pb2_grpc.add_KMeansServiceServicer_to_server(Mapper(num_reducers), server)
    server.add_insecure_port(f'localhost:{port}')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: mapper.py <num_reducers> <port>")
        sys.exit(1)

    num_reducers = int(sys.argv[1])
    port = int(sys.argv[2])
    serve_mapper(num_reducers, port)
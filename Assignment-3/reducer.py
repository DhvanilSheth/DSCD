import grpc
from concurrent import futures
import kmeans_pb2
import kmeans_pb2_grpc
import os
import sys
from collections import defaultdict

class Reducer(kmeans_pb2_grpc.KMeansServiceServicer):
    def __init__(self, reducer_id):
        self.reducer_id = reducer_id

    def ReduceTask(self, request, context):
        data_points = self._parse_data_points(request.data_points)

        shuffled_data = self._shuffle_and_sort(data_points)

        reduced_data = self._reduce_data(shuffled_data)

        self._write_to_file(reduced_data)

        return kmeans_pb2.ReducerResponse(
            reducer_id=self.reducer_id,
            success=True,
            message="Reducing completed successfully."
        )

    def _parse_data_points(self, data_points):
        return {point.id: [coordinate for coordinate in point.coordinates] for point in data_points}

    def _shuffle_and_sort(self, data_points):
        shuffled_data = defaultdict(list)
        for key, point in data_points.items():
            shuffled_data[key].append(point)
        return dict(sorted(shuffled_data.items()))

    def _reduce_data(self, shuffled_data):
        reduced_data = {}
        for key, points in shuffled_data.items():
            reduced_data[key] = [sum(x) / len(x) for x in zip(*points)]
        return reduced_data

    def _write_to_file(self, reduced_data):
        os.makedirs(f'Data/Reducers/R{self.reducer_id}', exist_ok=True)
        with open(f'Data/Reducers/R{self.reducer_id}/reducer_{self.reducer_id}_output.txt', 'w') as f:
            for key, centroid in reduced_data.items():
                f.write(f'{key} {" ".join(map(str, centroid))}\n')

def serve_reducer(reducer_id, port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kmeans_pb2_grpc.add_KMeansServiceServicer_to_server(Reducer(reducer_id), server)
    server.add_insecure_port(f'localhost:{port}')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: reducer.py <reducer_id> <port>")
        sys.exit(1)

    reducer_id = int(sys.argv[1])
    port = int(sys.argv[2])
    serve_reducer(reducer_id, port)
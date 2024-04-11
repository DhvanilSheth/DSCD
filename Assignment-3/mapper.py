import grpc
from concurrent import futures
import kmeans_pb2
import kmeans_pb2_grpc
import json

# Assuming you have 'kmeans_pb2' and 'kmeans_pb2_grpc' from the generated gRPC code.

class Mapper(kmeans_pb2_grpc.KMeansServiceServicer):
    def __init__(self):
        # Initialize necessary variables such as the current centroids
        self.centroids = []

    def MapTask(self, request, context):
        # Parse the request
        mapper_id = request.mapper_id
        data_points = json.loads(request.input_data)
        centroids = self._parse_centroids(request.centroids)
        
        # Perform mapping
        mapped_data = self._map_data(data_points, centroids)
        
        # Write to local file system
        self._write_to_file(mapped_data, mapper_id)

        # Partition the data
        partitions = self._partition_data(mapped_data)

        # Write the partitions to local file system
        self._write_partitions(partitions, mapper_id)

        # Return a successful response
        return kmeans_pb2.MapperResponse(
            mapper_id=mapper_id,
            success=True,
            message="Mapping and partitioning completed successfully."
        )

    def _parse_centroids(self, centroids):
        # Convert the centroids from the request to a usable format
        return [[coordinate for coordinate in point.coordinates] for point in centroids]

    def _map_data(self, data_points, centroids):
        # Map the data points to the nearest centroid
        # This is where the core of the K-Means algorithm is implemented
        mapped_data = {}
        # Pseudocode for mapping data points to centroids:
        for point in data_points:
            # Determine the nearest centroid
            # Assign point to the nearest centroid's list
            pass
        return mapped_data

    def _write_to_file(self, mapped_data, mapper_id):
        # Write the mapping results to a file on the local filesystem
        pass

    def _partition_data(self, mapped_data):
        # Partition the data based on the number of reducers
        # Each partition corresponds to one reducer
        partitions = {}
        # Pseudocode for partitioning:
        for key, points in mapped_data.items():
            # Determine the appropriate reducer for this key
            # Add the key-value pair to the corresponding partition
            pass
        return partitions

    def _write_partitions(self, partitions, mapper_id):
        # Write the partitions to separate files on the local filesystem
        pass

# Function to serve the Mapper server using gRPC
def serve_mapper():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kmeans_pb2_grpc.add_KMeansServiceServicer_to_server(Mapper(), server)
    
    # You will need to assign a unique port for each mapper server
    server.add_insecure_port('[::]:50052')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve_mapper()

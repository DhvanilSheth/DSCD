from sklearn.cluster import KMeans
import numpy as np

def load_data(file_path):
    data = np.loadtxt(file_path, delimiter=',')
    return data

def perform_kmeans(data, num_centroids):
    kmeans = KMeans(n_clusters=num_centroids, random_state=0).fit(data)
    return kmeans.cluster_centers_

def main():
    file_path = 'points.txt'
    num_centroids = 5
    data = load_data(file_path)
    centroids = perform_kmeans(data, num_centroids)
    print("Centroids: ", centroids)

if __name__ == "__main__":
    main()
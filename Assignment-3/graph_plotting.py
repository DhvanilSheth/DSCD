import matplotlib.pyplot as plt
import numpy as np

def plot_points(file_name, centroid_file):
    with open(file_name, 'r') as file:
        data = file.read().splitlines()
    x = []
    y = []
    for i in range(len(data)):
        # Split the line into components, remove commas, and convert to float
        point = data[i].replace(',', '').split()
        x.append(float(point[0]))
        y.append(float(point[1]))
    plt.scatter(x, y)

    # Plotting centroids in red
    with open(centroid_file, 'r') as file:
        centroids = file.read().splitlines()
    centroid_x = []
    centroid_y = []
    for centroid in centroids:
        point = centroid.replace(',', '').split()
        centroid_x.append(float(point[0]))
        centroid_y.append(float(point[1]))
    plt.scatter(centroid_x, centroid_y, color='red')

    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.title('Scatter Plot with Centroids')
    plt.show()

if __name__ == '__main__':
    plot_points('Data//Input//5_Clusters_input.txt', 'Data//Output//5_Clusters_output.txt')
    # plot_points('Data//Input//5_Clusters_input.txt', 'Data//centroids.txt')
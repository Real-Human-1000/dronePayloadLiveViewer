import numpy as np
import matplotlib.pyplot as plt
import scipy
from shutil import rmtree, copy
import os
from time import sleep

# This all could be done much more easily using Pandas

filename = "Particle Element Analysis - MaxData.csv"

special_conversions = {
    "Sample": {"S1-D": 1, "S2-D": 2, "S3-D": 3, "S4-D": 4, "S5-D": 5},
    "Fireworks": {"None": 0.0, "Smoke": 0.33, "Moderate": 0.66, "Finale": 1.0},
    "Unit Shape": {"Round": 0.0, "Lumpy": 0.5, "Angular": 1.0},
    "Conglomerate?": {"FALSE": 0.0, "TRUE": 1.0},
    "Surface": {"Smooth": 0.0, "HF Rough": 0.33, "LF Rough": 0.66, "Foamy": 1.0},
    "Phys. Abnor.?": {"FALSE": 0.0, "TRUE": 1.0},
    "Comp. Abnor.?": {"FALSE": 0.0, "TRUE": 1.0}
}

exclude_columns = [
    "Name", "Sample", "Fireworks", "Distance", "Minor Dia. (um)",
    "Major dia. (um)",
    "Unit Shape", "Conglomerate?",
    "Aspect Ratio",
    "Surface",
    "Phys. Abnor.?", "Comp. Abnor.?",
    #"Na", "K", "Cs", "Mg", "Ca", "Sr", "Ba", "Ti", "Cr", "Fe", "Ir", "Cu", "Al", "Ga", "C",
    #"Si",
    #"N",
    "P",
    #"O", "S", "Cl", "Br",
    "Alk. Metals", "Alk. Earth Metals", "Trans. Metals ", "Post-Trans. Metals",
    "Nonmetals",
    "Metals",
    "Intermediate NM", "Corrosive NM\n",
    #"C",
    #"O"
]
exclude_columns_idx = []

headers = []
data = []
particle_names = []
with open(filename, 'r') as file:
    lines = file.readlines()
    for i in range(len(lines)):
        if i == 0:
            # Headers / Column Titles
            all_headers = lines[i].split(',')
            # Remove the selected columns
            for h in range(len(all_headers)):
                if all_headers[h] in exclude_columns:
                    exclude_columns_idx.append(h)
                else:
                    headers.append(all_headers[h])
        elif i > 1:
            data_in_line = lines[i].split(',')
            particle_names.append(data_in_line[0])
            data_to_keep = []
            for d in range(len(data_in_line)):
                if d not in exclude_columns_idx:
                    data_to_keep.append(data_in_line[d])
            data.append(data_to_keep)  # exclude the name/number of particle
            for d in range(len(data[-1])):
                # convert human-readable descriptors to values
                if len(data[-1][d]) == 0:
                    data[-1][d] = 0.0
                if headers[d] in special_conversions.keys() and data[-1][d] in special_conversions[headers[d]].keys():
                    data[-1][d] = special_conversions[headers[d]][data[-1][d]]
                data[-1][d] = float(data[-1][d])

print(headers)
print(data)

data_arr = np.array(data)

corr = np.corrcoef(data_arr.T)

fig = plt.figure()
ax = fig.add_subplot(111)
cax = ax.matshow(corr)
fig.colorbar(cax)

xaxis = np.arange(len(headers))
ax.set_xticks(xaxis)
ax.set_yticks(xaxis)
ax.set_xticklabels(headers, rotation=90)
ax.set_yticklabels(headers, rotation=0)

plt.tight_layout()
# plt.show()

whitened_data_arr = scipy.cluster.vq.whiten(data_arr)
codebook, distortion = scipy.cluster.vq.kmeans(whitened_data_arr, k_or_guess=10, iter=30)
# print(distortion)
rescaled_clusters = codebook * np.std(data_arr, 0)
# print(rescaled_clusters)

# Remove old clusters
try:
    rmtree("ClusteredParticleImages")
except FileNotFoundError:
    print("Didn't need to delete ClusteredParticleImages")
os.mkdir("ClusteredParticleImages")

# Figure out how many particles are in each cluster
particle_labels = {}
for row in range(data_arr.shape[0]):
    euclidian_distances = np.zeros((codebook.shape[0],))
    for c in range(codebook.shape[0]):
        difference_vector = rescaled_clusters[c,:] - data_arr[row,:]
        euclidian_distances[c] = np.sqrt(np.dot(difference_vector, difference_vector))
    nearest_cluster = int(np.argmin(euclidian_distances))
    if nearest_cluster not in particle_labels.keys():
        particle_labels[nearest_cluster] = []
    os.makedirs(os.path.join("ClusteredParticleImages", str(nearest_cluster)), exist_ok=True)
    particle_labels[nearest_cluster].append(particle_names[row])
    copy(os.path.join("ParticleImages", particle_names[row] + ".jpg"), os.path.join("ClusteredParticleImages", str(nearest_cluster), particle_names[row] + ".jpg"))
print(particle_labels)


with open("clusters.csv", 'w') as output_file:
    output_file.write(','.join(headers) + "\n")
    for row in range(rescaled_clusters.shape[0]):
        new_row_data = []
        for col in range(rescaled_clusters.shape[1]):
            if headers[col] in special_conversions.keys():
                # Find nearest label
                nearest_label = 0
                nearest_label_distance = np.inf
                for label, value in special_conversions[headers[col]].items():
                    if abs(rescaled_clusters[row,col] - value) < nearest_label_distance:
                        nearest_label = label
                        nearest_label_distance = abs(rescaled_clusters[row,col] - value)
                new_row_data.append(nearest_label)
            else:
                new_row_data.append(str(rescaled_clusters[row,col]))
        output_file.write(','.join(new_row_data) + "\n")
        #output_file.write(','.join([str(d) for d in rescaled_clusters[c,:].flatten().tolist()]) + "\n")

# {4: ['1', '16'], 5: ['2', '14', '15'], 6: ['3', '8 (over)', '21'], 3: ['4', '5 (up)', '5 (down)', '19'], 7: ['6', '11', '12', '13', '17', '18'], 2: ['7', '22'], 0: ['8 (under)'], 1: ['9', '10', '20']}
# {1: ['1', '3', '4', '6', '7', '8 (over)', '16', '17', '18'], 7: ['2', '5 (up)', '5 (down)', '14', '15', '19'], 2: ['8 (under)'], 3: ['9', '10', '20'], 4: ['11', '12'], 0: ['13'], 5: ['21'], 6: ['22']}

import matplotlib.pyplot as plt
import os
from random import random
import numpy as np

# Settings as used during tests (don't mess with this)
coding_rates = [8, 7, 6, 5]
spreading_factors = [12, 11, 10, 9, 8, 7]#, 6};
#long bandwidths[10] = {500000, 250000, 125000, 62500, 41700, 31250, 20800, 15600, 10400, 7800};
bandwidths = [125000, 62500, 250000, 41700, 500000, 31250]#, 20800, 15600, 10400, 7800};


# Function for converting a setting index into coding_rate
def get_coding_rate(index):
    return coding_rates[int(index) % 4]


# Function for converting a setting index into spreading_factor
def get_spreading_factor(index):
    return spreading_factors[int(index / 4) % 7]


# Function for converting a setting index into bandwidth
def get_bandwidth(index):
    return bandwidths[int(index / (4 * 7)) % 10]


# PARAMETERS:
# first test / log_2025-07-17_13-29-18.json or second test / log_2025-07-17_13-47-09.json
log_filename = os.path.join("../server/raw_serial_logs", f"log_2025-07-17_13-47-09.json")
dependent_var = "SNR"  # RSSI, SNR, or freq_error
dependent_var_nice = "Frequency Error" if dependent_var == "freq_error" else dependent_var
horiz_dist = 1086  # 627 (first test / log_2025-07-17_13-29-18.json) or 1086 (second test / log_2025-07-17_13-47-09.json)
altitude = 350
jitter = 0.0
separation = 0.0
selected_bandwidth = 125000  # 125000 is the only one we have complete data for


with open(log_filename, 'r') as file:
    lines = file.readlines()

data_points = []
# {"setting_idx": #, "initiator_points": [{}, {}], "responder_points": [{}, {}]}
setting_change_idx = 0
current_setting = 0
last_setting = 0
for i in range(len(lines)):
    # print(f"Loading line {i}")
    if lines[i][:len("Changing to setting ")] == "Changing to setting ":
        setting_change_idx = i
        current_setting = int(lines[i][len("Changing to setting "):])
        last_setting = max(current_setting, last_setting)
        data_points.append({"setting_idx": current_setting, "initiator_points": [], "responder_points": []})
    if lines[i][:len("lastSNR: ")] == "lastSNR: ":
        metric_strings = lines[i].split(", ")
        SNR = int(metric_strings[0][len("lastSNR: "):])
        freq_error = int(metric_strings[1][len("fError: "):])
        RSSI = int(metric_strings[2][len("lastRSSI: "):])
        data_points[current_setting]["initiator_points"].append({"SNR": SNR, "RSSI": RSSI, "freq_error": freq_error})
    if lines[i][:len("Got SNR: ")] == "Got SNR: ":
        metric_strings = lines[i].split(", ")
        SNR = int(metric_strings[0][len("Got SNR: "):])
        freq_error = int(metric_strings[1][len("Got fError: "):])
        RSSI = int(metric_strings[2][len("Got RSSI: "):])
        data_points[current_setting]["responder_points"].append({"SNR": SNR, "RSSI": RSSI, "freq_error": freq_error})

print(data_points)

xi = []
yi = []
zi = []
ci = []
xr = []
yr = []
zr = []
cr = []
for i in range(last_setting):
    if abs(get_bandwidth(i) - selected_bandwidth) < 100:
        if len(data_points[i]["initiator_points"]) > 0:
            xi.append(get_coding_rate(data_points[i]["setting_idx"]) + jitter*(2*random()-1) - separation)
            yi.append(get_spreading_factor(data_points[i]["setting_idx"]) + jitter*(2*random()-1) - separation)
            zi.append(get_bandwidth(data_points[i]["setting_idx"]) + jitter*(2*random()-1) - separation)
            ci.append(data_points[i]["initiator_points"][0][dependent_var])
        if len(data_points[i]["responder_points"]) > 0:
            xr.append(get_coding_rate(data_points[i]["setting_idx"]) + jitter*(2*random()-1) + separation)
            yr.append(get_spreading_factor(data_points[i]["setting_idx"]) + jitter*(2*random()-1) + separation)
            zr.append(get_bandwidth(data_points[i]["setting_idx"]) + jitter*(2*random()-1) + separation)
            cr.append(data_points[i]["responder_points"][0][dependent_var])


# r_cmap = plt.get_cmap('Reds')
# sctt = ax.scatter3D(x, y, z, c=c)
# sctt = ax.scatter(x, y, c=c)
# fig.colorbar(sctt, ax=ax)


def make_contour(x, y, c, descriptor):
    fig = plt.figure()
    ax = plt.axes()  # projection='3d')
    # make a contour for a single bandwidth
    x_min = min(x)
    y_min = min(y)
    x_max = max(x)
    y_max = max(y)
    print(x_min, x_max, y_min, y_max)
    X = np.zeros((int(x_max - x_min + 1), int(y_max - y_min + 1)))
    n_rows = X.shape[0]
    n_cols = X.shape[1]
    Y = np.zeros_like(X)
    C = np.ones_like(X)
    for i in range(len(x)):
        # print(n_cols * (y[i] - y_min) / ((y_max + 1) - y_min), n_rows * (x[i] - x_min) / ((x_max + 1) - x_min))
        X[int(n_rows * (x[i] - x_min) / ((x_max + 1) - x_min)), int(n_cols * (y[i] - y_min) / ((y_max + 1) - y_min))] = x[i]
        Y[int(n_rows * (x[i] - x_min) / ((x_max + 1) - x_min)), int(n_cols * (y[i] - y_min) / ((y_max + 1) - y_min))] = y[i]
        C[int(n_rows * (x[i] - x_min) / ((x_max + 1) - x_min)), int(n_cols * (y[i] - y_min) / ((y_max + 1) - y_min))] = c[i]

    cont = ax.contourf(X, Y, C, levels=100)
    cbar = fig.colorbar(cont, ax=ax)
    cbar.set_label(f"{dependent_var_nice}", rotation=270, labelpad=15)

    ax.set_xlabel("Coding Rate")
    ax.set_ylabel("Spreading Factor")
    # ax.set_zlabel("Bandwidth")

    # fig.suptitle(f"{dependent_var_nice} vs Coding Rate, Spreading Factor, and Bandwidth")
    fig.suptitle(f"{dependent_var_nice} vs CR and SF at BW {selected_bandwidth} Hz\n{descriptor}")

    plt.show()


make_contour(xi, yi, ci, descriptor=f"for Initiator at {horiz_dist} ft horiz, {altitude} ft vert distance (total {(horiz_dist**2 + altitude**2)**0.5:.01f} ft)")
make_contour(xr, yr, cr, descriptor=f"for Responder at {horiz_dist} ft horiz, {altitude} ft vert distance (total {(horiz_dist**2 + altitude**2)**0.5:.01f} ft)")

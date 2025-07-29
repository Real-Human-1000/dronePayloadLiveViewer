import matplotlib.pyplot as plt
import json
import numpy as np
# Graph the data log collected by the sensor suite


def load_log(filename):
    # Load a log file (JSON line-by-line) and return it as a list of dictionaries
    # Returns list of dictionaries
    with open(filename, 'r') as file:
        data = [json.loads(l) for l in file.readlines()]
    return data


def graph_simple(log_data, independent_var, dependent_vars):
    # Graph one or two dependent variables (vertical axis) against one independent variable (horizontal axis)
    assert 1 <= len(dependent_vars) <= 2

    fig, ax1 = plt.subplots()
    ax1.set_xlabel(independent_var)
    ax1.set_ylabel(dependent_vars[0], color="tab:red")
    ax1.plot([d["data"][0][independent_var] for d in log_data if d["type"] == 'D' and independent_var in d["data"][0]],
             [d["data"][0]["sensors"][dependent_vars[0]] for d in log_data if d["type"] == 'D' and dependent_vars[0] in d["data"][0]["sensors"] and dependent_vars[1] in d["data"][0]["sensors"]],
             color="tab:red")
    ax1.tick_params(axis='y', labelcolor="tab:red")
    #ax1.set_ylim([0, 2000])

    if len(dependent_vars) == 2:
        ax2 = ax1.twinx()
        ax2.set_xlabel(independent_var)
        ax2.set_ylabel(dependent_vars[1], color="tab:blue")
        ax2.plot([d["data"][0][independent_var] for d in log_data if d["type"] == 'D'],
                 [d["data"][0]["sensors"][dependent_vars[1]] for d in log_data if d["type"] == 'D'],
                 color="tab:blue")
        ax2.tick_params(axis='y', labelcolor="tab:blue")
        #ax2.set_ylim([0, 10000])
        plt.title(f"{dependent_vars[0]} and {dependent_vars[1]} vs {independent_var}")
    else:
        plt.title(f"{dependent_vars[0]} vs {independent_var}")

    # Add annotations for user notes
    for n in [d for d in log_data if d["type"] == "N" and "Ground altitude changed to " not in d["value"]]:
        ax1.text(n["interptime"], 0.5 * ax1.get_ylim()[0] + 0.5 * ax1.get_ylim()[1], n["value"], fontsize=6, rotation=90, rotation_mode="anchor")

    fig.tight_layout()
    plt.show()


def graph_altitude(log_data, dependent_vars, graph_in_feet=False):
    # Graph one or two independent variables (horizontal axis) against altitude (vertical axis)
    # Order points by altitude to remove time differences
    assert 1 <= len(dependent_vars) <= 2

    fig, ax1 = plt.subplots()
    ax1.set_ylabel(f"Altitude ({'ft' if graph_in_feet else 'm'})")
    ax1.set_xlabel(dependent_vars[0], color="tab:red")

    altitude_data = [d["data"][0]["altitude"] for d in log_data if d["type"] == 'D']
    sort_idx = np.argsort(np.array(altitude_data))
    sorted_altitude_data = np.array(altitude_data)[sort_idx]
    sorted_altitude_data = sorted_altitude_data - sorted_altitude_data[0]
    if graph_in_feet:
        sorted_altitude_data = sorted_altitude_data * 3.28084

    dependent_data_1 = [d["data"][0]["sensors"][dependent_vars[0]] for d in log_data if
              d["type"] == 'D' and dependent_vars[0] in d["data"][0]["sensors"] and (len(dependent_vars) == 1 or dependent_vars[1] in d["data"][0]["sensors"])]
    # make sure this isn't a message or corrupt packet
    sorted_dependent_data_1 = np.array(dependent_data_1)[sort_idx]

    ax1.plot(sorted_dependent_data_1,
             sorted_altitude_data,
             color="tab:red")
    ax1.tick_params(axis='x', labelcolor="tab:red")
    ax1.set_xlim([0,2450])

    if len(dependent_vars) == 2:
        dependent_data_2 = [d["data"][0]["sensors"][dependent_vars[1]] for d in log_data if
              d["type"] == 'D' and dependent_vars[0] in d["data"][0]["sensors"] and dependent_vars[1] in d["data"][0]["sensors"]]
        sorted_dependent_data_2 = np.array(dependent_data_2)[sort_idx]

        ax2 = ax1.twiny()
        ax2.set_xlabel(dependent_vars[1], color="tab:blue")
        ax2.set_ylabel(f"Altitude ({'ft' if graph_in_feet else 'm'})")
        ax2.plot(sorted_dependent_data_2, sorted_altitude_data, color="tab:blue")
        ax2.tick_params(axis='x', labelcolor="tab:blue")
        ax2.set_xlim([0, 340])

        plt.title(f"{dependent_vars[0]} and {dependent_vars[1]} vs Altitude")
    else:
        plt.title(f"{dependent_vars[0]} vs Altitude")

    fig.tight_layout()
    plt.show()


def main():
    log_filename = "../server/logs/log_2025-07-04_21-44-57.json"
    log_data = load_log(log_filename)

    independent_var = "altitude"
    dependent_vars = ["CO2"]

    # graph_simple(log_data, independent_var, dependent_vars)

    graph_altitude(log_data, dependent_vars, graph_in_feet=True)


if __name__ == "__main__":
    main()


# PM03 and PM05 have a lot of false positives
# PM10 and above seem to be good at detecting smoke
# CO2 basically doesn't respond at all
# TVOC & eCO2 are sporadic at best and easily fooled

# Baseline/neutral values:
# CO2:  400-550, 400-600
# TVOC: 0-100, maybe 50-150
# eCO2: 400-550, maybe 400-600
# PM03: 500-1200, maybe 800-6000 in weird situations
# PM05: 200-400, maybe 100-1200 in weird situations
# PM10: 0-60, 40-60
# PM25: 0-25, 0-30
# PM50: 0-10, 0-8

# Elevated values
# CO2: 6000 when breathing on it
# TVOC: 200-4000?
# eCO2: 800-1500? sus
# PM03: 15000-65000? check num zeros
# PM05: 4800-26000
# PM10: 650-14500
# PM25: 125-4500
# PM50: 14-1350
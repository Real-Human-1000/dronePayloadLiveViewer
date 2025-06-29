import matplotlib.pyplot as plt
import json
# Graph the data log collected by the sensor suite


def load_log(filename):
    # Load a log file (JSON line-by-line) and return it as a list of dictionaries
    # Returns list of dictionaries
    with open(filename, 'r') as file:
        data = [json.loads(l) for l in file.readlines()]
    return data


def main():
    log_filename = "logs\\log_2025-06-26_09-21-33.json"
    log_data = load_log(log_filename)

    independent_var = "interptime"
    dependent_vars = ["PM50"]
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

    assert 1 <= len(dependent_vars) <= 2

    fig, ax1 = plt.subplots()
    ax1.set_xlabel(independent_var)
    ax1.set_ylabel(dependent_vars[0], color="tab:red")
    ax1.plot([d["data"][0][independent_var] for d in log_data if d["type"] == 'D'],
             [d["data"][0]["sensors"][dependent_vars[0]] for d in log_data if d["type"] == 'D'],
             color="tab:red")
    ax1.tick_params(axis='y', labelcolor="tab:red")

    if len(dependent_vars) == 2:
        ax2 = ax1.twinx()
        ax2.set_xlabel(independent_var)
        ax2.set_ylabel(dependent_vars[1], color="tab:blue")
        ax2.plot([d["data"][0][independent_var] for d in log_data if d["type"] == 'D'],
                 [d["data"][0]["sensors"][dependent_vars[1]] for d in log_data if d["type"] == 'D'],
                 color="tab:blue")
        ax2.tick_params(axis='y', labelcolor="tab:blue")
        plt.title(f"{independent_var} vs {dependent_vars[0]} and {dependent_vars[1]}")
    else:
        plt.title(f"{independent_var} vs {dependent_vars[0]}")

    # Add annotations for user notes
    for n in [d for d in log_data if d["type"] == "N"]:
        ax1.text(n["interptime"], 0.5 * ax1.get_ylim()[0] + 0.5 * ax1.get_ylim()[1], n["value"], fontsize=6, rotation=90, rotation_mode="anchor")

    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
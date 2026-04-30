import pandas as pd
import yaml
from FaultTree.FTParser import *
from Algorithms.WorstCase import WorstCost
from Algorithms.allcost import WorstCostTrue
import os
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
from matplotlib.ticker import PercentFormatter

def load_config(yaml_file="run_config.yaml"):
    with open(yaml_file, "r") as f:
        return yaml.safe_load(f)


def load_csv(file, metric):
    df = pd.read_csv(file)
    df[metric] = pd.to_numeric(df[metric], errors="coerce")
    df = df.dropna(subset=["FT", metric])
    return df.sort_values(by=["FT"])


def obtain_worst_case(filename):
    FT = FTParse(filename)
    FT.unreliability(add_unreliability=True)
    wc = WorstCostTrue(FT)
    return wc


def calc_ratio(files, metric):
    data1 = load_csv(files[0], metric)
    data2 = load_csv(files[1], metric)
    ratio = []

    for a, b in zip(data1[metric], data2[metric]):
        ratio.append(a/b)
    return ratio


def calc_wc(folder, fts):
    worstcase = []
    # print(fts)
    for fname in os.listdir(folder):
        # print(fname)
        # print(str(fname) in fts)
        if fname in fts:
            wc = obtain_worst_case(os.path.join(folder, fname))
            worstcase.append(wc)
    return worstcase


def plot_wc_no_limit(ratio, worst):
    plt.scatter(ratio, worst, c="#4C72B0")
    # plt.xlim(0, 10e2)
    # plt.ylim(0, 10e2)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Measured ratio")
    plt.ylabel("Worst case ratio")
    plt.title("Worst case ratio vs Measured ratio")
    plt.show()


def plot_wc(ratio, worst, limit=[3e1, 3e1]):
    import numpy as np

    ratio = np.array(ratio)
    worst = np.array(worst)

    over_x = ratio > limit[0]
    over_y = worst > limit[1]
    normal = ~(over_x | over_y)

    ratio_clipped = np.minimum(ratio, limit[0])
    worst_clipped = np.minimum(worst, limit[1])

    plt.figure()

    # Normal points
    plt.scatter(
        ratio_clipped[normal],
        worst_clipped[normal],
        color="blue",
        alpha=0.7,
        label="Inside limit"
    )

    # Points exceeding x-limit (color by true ratio value)
    sc_x = plt.scatter(
        ratio_clipped[over_x],
        worst_clipped[over_x],
        c=ratio[over_x],              # color depends on real ratio
        cmap="Reds",
        marker=">",
        s=80,
        label="Ratio overflow"
    )

    # Points exceeding y-limit (color by true worst value)
    sc_y = plt.scatter(
        ratio_clipped[over_y],
        worst_clipped[over_y],
        c=worst[over_y],
        cmap="Greens",
        norm=LogNorm(vmin=limit[1], vmax=worst.max()),
        marker="^",
        s=80,
        label="Worst overflow"
    )

    plt.xscale("log")
    plt.yscale("log")
    plt.xlim(0.9e0, limit[0])
    plt.ylim(0.9e0, limit[1])

    plt.colorbar(sc_x, label="True Ratio (overflow)")
    plt.colorbar(sc_y, label="True Worst (overflow)")

    plt.legend()
    plt.show()



def run_wc(config):
    files = config.get("folder", [])
    ratio = calc_ratio(files, "expcost")
    data = load_csv(files[0], "expcost")
    names = data["FT"].to_list()
    worst = calc_wc(files[2], names)
    limit = config.get("limit", None)
    if config.get("limit"):
        limit = [float(x) for x in limit]
        plot_wc(ratio, worst, limit)
    else:
        plot_wc_no_limit(ratio, worst)

def run_wc_alt(config, threshold=1.5):
    files = config.get("folder", [])
    ratio = np.array(calc_ratio(files, "expcost"))
    data = load_csv(files[0], "expcost")
    names = data["FT"].to_list()
    worst = np.array(calc_wc(files[2], names))
    # Create mask for valid (non-None) worst values
    valid_mask = np.array([w is not None for w in worst])

    # Filter arrays
    ratio = ratio[valid_mask]
    worst = worst[valid_mask].astype(float)
    TP = TN = FP = FN = 0

    TP = np.sum((ratio < threshold) & (worst < threshold))
    TN = np.sum((ratio >= threshold) & (worst >= threshold))
    FP = np.sum((ratio < threshold) & (worst >= threshold))
    FN = np.sum((ratio >= threshold) & (worst < threshold))

    confusion_matrix = np.array([
        [TP, FN],
        [FP, TN]
    ])

    total = TP + TN + FP + FN
    accuracy = (TP + TN) / total if total > 0 else 0
    precision = TP/ (TP + FP) if (TP + FP) > 0 else 0
    recall = TP/(TP+FN) if (TP+FN) > 0 else 0
    oprecall = TN/(TN+FP) if (TN+FN) > 0 else 0
    return {
        "WC low": TP,
        "WC high": TN,
        "WC high ratio low": FP,
        "WC low ratio high": FN,
        "confusion_matrix": confusion_matrix,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "oprecall": oprecall

    }


def plot_accuracy_vs_threshold(config, metric, min_threshold=1.0, max_threshold=2.0, step=0.01):
    thresholds = np.arange(min_threshold, max_threshold + step, step)
    accuracies = []

    for t in thresholds:
        results = run_wc_alt(config, threshold=t)
        accuracies.append(results[metric])

    accuracies = np.array(accuracies)

    # Find best threshold
    best_idx = np.argmax(accuracies)
    best_threshold = thresholds[best_idx]
    best_accuracy = accuracies[best_idx]

    plt.figure(figsize=(10, 6))
    plt.scatter(thresholds, accuracies)
    # plt.scatter(best_threshold, best_accuracy, zorder=5)

    plt.title(f"{metric} vs Threshold", fontsize=16)
    plt.xlabel("Threshold", fontsize=12)

    plt.ylabel(f"{metric}", fontsize=12)
    plt.gca().yaxis.set_major_formatter(PercentFormatter(1.0))
    plt.grid(alpha=0.3)
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.show()

    return best_threshold, best_accuracy


if __name__ == "__main__":
    config = load_config()
    # run_wc(config)
    # results = run_wc_alt(config)
    plot_accuracy_vs_threshold(config, "accuracy")
    # print(run_wc_alt(config, 1.26))



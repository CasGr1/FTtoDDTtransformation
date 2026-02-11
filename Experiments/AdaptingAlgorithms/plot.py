import matplotlib.pyplot as plt
import pandas as pd
import yaml
import os
import numpy as np
import statistics
import math

# ------------------ Config loading ------------------

def load_yaml_config(path="plot_config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

# ------------------ Data helpers ------------------

def load_csv(folder, name, addition, metric):
    df = pd.read_csv(os.path.join(folder, f"{name}{addition}.csv"))
    df[metric] = pd.to_numeric(df[metric], errors="coerce")
    return df.sort_values(by=["FT"])

def load_data_in_10s(file, column):
    data = pd.read_csv(file)
    data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=[column, "bes"])

    max_be = int(data["bes"].max())
    n_bins = math.ceil((max_be + 1) / 10)

    buckets = [[] for _ in range(n_bins)]
    for _, row in data.iterrows():
        bucket_idx = int(row["bes"] // 10)
        buckets[bucket_idx].append(float(row[column]))

    return tuple(buckets)

# ------------------ Dispatcher ------------------

def run_from_yaml(cfg):
    active = cfg["active_plot"]
    plot_cfg = dict(cfg["plots"][active])  # copy

    # merge global data config
    data_cfg = cfg.get("data", {})
    plot_cfg.setdefault("folder", data_cfg.get("folder"))
    plot_cfg.setdefault("addition", data_cfg.get("addition"))

    if plot_cfg["type"] == "xy":
        fig = run_xy_plot(plot_cfg)
        handle_output(
            fig,
            plot_cfg.get("output", cfg.get("output", {})),
            default_name=plot_cfg.get("name", "xy_plot")
        )

    elif plot_cfg["type"] == "summary":
        fig = plot_every_algorithm(plot_cfg)
        handle_output(
            fig,
            plot_cfg.get("output", cfg.get("output", {})),
            default_name=plot_cfg.get("name", "summary_plot")
        )

# ------------------ XY plots ------------------

def run_xy_plot(cfg):
    pairs = cfg["pairs"]
    metric = cfg["metric"]

    if "layout" in cfg:
        rows, cols = cfg["layout"]
        fig, axes = plt.subplots(
            rows, cols,
            figsize=(6 * cols, 5 * rows),
            squeeze=False
        )
        axes = axes.flatten()
    else:
        fig, ax = plt.subplots(figsize=(8, 6))
        axes = [ax]

    if len(axes) < len(pairs):
        raise ValueError("Not enough subplots for given pairs")

    for ax, (name1, name2) in zip(axes, pairs):
        d1 = load_csv(cfg["folder"], name1, cfg["addition"], metric)
        d2 = load_csv(cfg["folder"], name2, cfg["addition"], metric)

        plot_x_y(
            d1, d2,
            metric=metric,
            log=cfg.get("log", False),
            name1=name1,
            name2=name2,
            failure=cfg.get("failure", False),
            ax=ax,
            xyline=cfg.get("xyline", True)
        )

    if cfg.get("tight", True):
        fig.tight_layout()

    return fig

def plot_x_y(data1, data2, metric, log, name1, name2, failure, ax, xyline=True):
    vals = data1[metric].dropna()
    if xyline and not vals.empty:
        maxvalue = vals.max()
        minvalue = vals.min()

    ax.scatter(data1[metric], data2[metric], edgecolors="none")

    if "cost" in metric:
        ax.set_xlabel(f"expected cost {name1}")
        ax.set_ylabel(f"expected cost {name2}")
        title = f"Expected cost comparison of {name1} vs {name2}"
    elif "time" in metric:
        ax.set_xlabel(f"runtime (s) {name1}")
        ax.set_ylabel(f"runtime (s) {name2}")
        title = f"Runtime comparison of {name1} vs {name2}"
    else:
        title = f"{metric}: {name1} vs {name2}"

    if failure:
        title += " given failure"

    ax.set_title(title)

    if xyline and not vals.empty:
        if log:
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.plot(
                np.linspace(1, maxvalue * 1.05),
                np.linspace(1, maxvalue * 1.05),
                c="red"
            )
            ax.set_xlim(1, maxvalue * 1.05)
            ax.set_ylim(1, maxvalue * 1.05)
        else:
            ax.plot(
                np.linspace(minvalue * 0.95, maxvalue * 1.05),
                np.linspace(minvalue * 0.95, maxvalue * 1.05),
                c="red"
            )
            ax.set_xlim(minvalue * 0.95, maxvalue * 1.05)
            ax.set_ylim(minvalue * 0.95, maxvalue * 1.05)

# ------------------ Summary plots ------------------

def plot_every_algorithm(cfg):
    files = [
        os.path.join(cfg["folder"], name + cfg["addition"] + ".csv")
        for name in cfg["names"]
    ]

    all_data = [load_data_in_10s(file, cfg["metric"]) for file in files]
    max_buckets = max(len(d) for d in all_data)

    ft_labels = [f"{i*10+1}-{(i+1)*10}" for i in range(max_buckets)]
    x = np.arange(max_buckets)

    fig, ax = plt.subplots(figsize=(8, 6))

    plottype = cfg.get("plottype", "bar")
    pltdata = cfg.get("pltdata", "median")

    bar_width = 0.8 / len(files) if plottype == "bar" else None

    for i, (data, name) in enumerate(zip(all_data, cfg["names"])):

        if pltdata == "median":
            plotdata = [statistics.median(lst) if lst else float("nan") for lst in data]
        elif pltdata == "avg":
            plotdata = [statistics.mean(lst) if lst else float("nan") for lst in data]
        else:
            raise ValueError(f"Unknown pltdata: {pltdata}")

        plotdata += [float("nan")] * (max_buckets - len(plotdata))
        data_padded = list(data) + [[]] * (max_buckets - len(data))

        if plottype == "bar":
            ax.bar(
                x - 0.4 + bar_width / 2 + i * bar_width,
                plotdata,
                width=bar_width,
                label=name
            )
        elif plottype == "scatter":
            ax.scatter(x, plotdata, marker="_", label=name)
        elif plottype == "box":
            positions = x - 0.4 + 0.4 / len(files) + i * 0.4 / len(files)
            ax.boxplot(
                data_padded,
                positions=positions,
                widths=0.4 / len(files),
                patch_artist=True,
                medianprops=dict(color="black"),
                showfliers=True
            )

    ax.set_xticks(x)
    ax.set_xticklabels(ft_labels)
    ax.set_xlabel("#BE")

    if "time" in cfg["metric"]:
        ax.set_ylabel("Runtime (s)")
    elif "cost" in cfg["metric"]:
        ax.set_ylabel("Expected Cost")
    else:
        ax.set_ylabel(cfg["metric"])

    ax.legend()
    fig.tight_layout()

    return fig

# ------------------ Output ------------------

def handle_output(fig, output_cfg, default_name="figure"):
    show = output_cfg.get("show", True)
    save = output_cfg.get("save", False)

    if save:
        outdir = output_cfg.get("dir", "figures")
        os.makedirs(outdir, exist_ok=True)

        fmt = output_cfg.get("format", "png")
        dpi = output_cfg.get("dpi", 300)
        fname = output_cfg.get("filename", default_name)

        path = os.path.join(outdir, f"{fname}.{fmt}")
        fig.savefig(path, dpi=dpi)
        print(f"Saved figure → {path}")

    if show:
        plt.show()
    else:
        plt.close(fig)

# ------------------ Main ------------------

if __name__ == "__main__":
    cfg = load_yaml_config("plot_config.yaml")
    run_from_yaml(cfg)

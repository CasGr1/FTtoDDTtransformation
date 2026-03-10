import os
import glob
import yaml
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from scipy.stats import gaussian_kde


def load_config(config_path="config.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_and_normalize_data(config_path="plot_config.yaml"):
    config = load_config(config_path)
    results_folder = config["output_folder"]

    csv_files = glob.glob(os.path.join(results_folder, "*.csv"))

    if len(csv_files) == 0:
        print("No CSV files found.")
        return None, None, config

    all_data = []
    ft_data = {}

    for file in csv_files:
        if "FT8" not in file:
            ft_name = os.path.splitext(os.path.basename(file))[0]
            df = pd.read_csv(file)

            if len(df) == 0:
                continue

            baseline_runtime = df.loc[df["height"] == 0, "runtime"].values[0]
            baseline_cost = df.loc[df["height"] == 0, "expcost_given_failure"].values[0]

            df["runtime_norm"] = df["runtime"] / baseline_runtime
            df["cost_norm"] = df["expcost_given_failure"] / baseline_cost
            df["ft_name"] = ft_name

            all_data.append(df)
            ft_data[ft_name] = df.sort_values("height")

    full_df = pd.concat(all_data, ignore_index=True)

    return full_df, ft_data, config

def darken_color(color, factor, brighten=0.5):
    """
    Darken a matplotlib color.
    factor=0 → original color
    factor=1 → very dark
    """
    rgb = np.array(mcolors.to_rgb(color))
    return tuple(rgb * (1 - 0.7 * factor))

def plot_figure(full_df, ft_data, config):
    plt.figure(figsize=(9, 7))

    highlight_fts = config.get("highlight_fts", [])
    plotted_heights = config.get("heights", [])

    heights = sorted(full_df["height"].unique())
    cmap = plt.get_cmap("tab10")  # or tab20 for >10 heights
    colors = {h: cmap(i % 10) for i, h in enumerate(heights)}

    highlight_colors = config.get("highlight_colors", [])
    # ==========================================================
    # Draw faint trajectories for ALL FTs restricted to plotted_heights
    # ==========================================================
    if config.get("faintline", False):
        for ft_name, df in ft_data.items():
            df_subset = df[df["height"].isin(plotted_heights)].sort_values("height")
            if len(df_subset) < 2:
                continue

            plt.plot(
                df_subset["runtime_norm"],
                df_subset["cost_norm"],
                color="gray",
                alpha=0.18,
                linewidth=0.8,
                zorder=1
            )

    # ==========================================================
    # Plot non-highlighted scatter points
    # ==========================================================
    for h in plotted_heights:
        subset = full_df[(full_df["height"] == h) & (~full_df["ft_name"].isin(highlight_fts))]
        if len(subset) == 0:
            continue
        plt.scatter(
            subset["runtime_norm"],
            subset["cost_norm"],
            label=f"depth {h}",  # only real labels here
            color=colors[h],
            edgecolors="black",
            linewidths=0.4,
            s=60,
            alpha=0.85,
            zorder=2
        )

    # ==========================================================
    # Highlighted FTs restricted to plotted_heights
    # ==========================================================
    # ==========================================================
    # Highlighted FTs – plot ALL heights with darker shades
    # ==========================================================
    highlight_colors = config.get("highlight_colors", [])

    for i, ft_name in enumerate(highlight_fts):

        if ft_name not in ft_data:
            print(f"Warning: {ft_name} not found.")
            continue

        df = ft_data[ft_name].sort_values("height")

        base_color = highlight_colors[i % len(highlight_colors)]

        heights = df["height"].values
        max_h = heights.max()

        # Draw trajectory
        plt.plot(
            df["runtime_norm"],
            df["cost_norm"],
            color=base_color,
            linewidth=1.8,
            alpha=0.8,
            zorder=4,
            label="_nolegend_"
        )

        # Draw points with darker shades
        for _, row in df.iterrows():
            h = row["height"]
            factor = h / max_h if max_h > 0 else 0
            point_color = darken_color(base_color, factor)

            plt.scatter(
                row["runtime_norm"],
                row["cost_norm"],
                color=point_color,
                edgecolors="black",
                linewidths=1.3,
                s=140,
                zorder=5,
                label="_nolegend_"
            )

    # ==========================================================
    # Final styling
    # ==========================================================
    plt.xlabel("Normalized Runtime")
    plt.ylabel("Normalized Expected Cost Given Failure")
    plt.title("Runtime vs Expected Cost (Normalized per FT)")

    plt.legend(title="Depth", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()



def print_avg_improvements_per_height(full_df):
    """
    Calculates and prints the average percentage improvement in
    runtime and expected cost per height relative to height 0.

    Improvement is computed as:
        (1 - normalized_value) * 100
    """

    print("\n=== Average Improvement per Height (relative to height 0) ===")

    heights = sorted(full_df["height"].unique())

    for h in heights:
        if h == 0:
            continue  # skip baseline

        subset = full_df[full_df["height"] == h]

        if len(subset) == 0:
            continue

        runtime_improvement = (1 - subset["runtime_norm"]) * 100
        cost_improvement = (1 - subset["cost_norm"]) * 100

        avg_runtime_impr = runtime_improvement.mean()
        avg_cost_impr = cost_improvement.mean()

        print(f"Depth {h}:")
        print(f"  Avg Runtime Improvement: {avg_runtime_impr:.2f}%")
        print(f"  Avg Cost Improvement:    {avg_cost_impr:.2f}%")
        print()

# def plot_figure_dedup_cost(full_df, ft_data, config):
#     """
#     Same as plot_figure(), but if an FT has the same
#     'expcost_given_failure' for multiple heights,
#     only the row with the largest height is plotted.
#     """
#
#     # -----------------------------
#     # Preprocess: remove duplicate cost per FT
#     # -----------------------------
#     filtered_ft_data = {}
#     filtered_rows = []
#
#     for ft_name, df in ft_data.items():
#         # Sort by height so largest height comes last
#         df_sorted = df.sort_values("height")
#
#         # For duplicate costs, keep the largest height
#         df_filtered = (
#             df_sorted
#             .sort_values("height")                # ascending
#             .drop_duplicates(
#                 subset=["expcost_given_failure"],
#                 keep="last"                       # keep largest height
#             )
#             .sort_values("height")
#         )
#
#         filtered_ft_data[ft_name] = df_filtered
#         filtered_rows.append(df_filtered)
#
#     filtered_full_df = pd.concat(filtered_rows, ignore_index=True)
#
#     # -----------------------------
#     # Begin plotting (same logic)
#     # -----------------------------
#     plt.figure(figsize=(9, 7))
#
#     highlight_fts = config.get("highlight_fts", [])
#     heights = sorted(filtered_full_df["height"].unique())
#     cmap = plt.get_cmap("tab20")
#     colors = {h: cmap(i % 20) for i, h in enumerate(heights)}
#     plotted_heights = config.get("heights")
#
#     # -----------------------------
#     # Plot non-highlighted FTs first
#     # -----------------------------
#     for h in heights:
#         if h in plotted_heights:
#             subset = filtered_full_df[filtered_full_df["height"] == h]
#
#             # exclude highlighted FTs
#             subset = subset[~subset["ft_name"].isin(highlight_fts)]
#
#             plt.scatter(
#                 subset["runtime_norm"],
#                 subset["cost_norm"],
#                 label=f"height {h}",
#                 color=colors[h],
#                 edgecolors="black",
#                 linewidths=0.5,
#                 s=60,
#                 alpha=0.8
#             )
#
#     # -----------------------------
#     # Plot highlighted FTs
#     # -----------------------------
#     for ft_name in highlight_fts:
#         if ft_name not in filtered_ft_data:
#             print(f"Warning: {ft_name} not found.")
#             continue
#
#         df = filtered_ft_data[ft_name]
#
#         # Draw thin colored line segments between heights
#         for i in range(len(df) - 1):
#             h = df.iloc[i]["height"]
#             plt.plot(
#                 df.iloc[i:i + 2]["runtime_norm"],
#                 df.iloc[i:i + 2]["cost_norm"],
#                 color=colors[h],
#                 linewidth=1.2,
#                 alpha=0.9
#             )
#
#         # Draw larger points
#         for _, row in df.iterrows():
#             plt.scatter(
#                 row["runtime_norm"],
#                 row["cost_norm"],
#                 color=colors[row["height"]],
#                 edgecolors="black",
#                 linewidths=1.2,
#                 s=120,
#                 zorder=5
#             )
#
#     plt.xlabel("Normalized Runtime")
#     plt.ylabel("Normalized Expected Cost Given Failure")
#     plt.title("Runtime vs Expected Cost (Normalized per FT)")
#     plt.legend(title="Height", bbox_to_anchor=(1.05, 1), loc="upper left")
#
#     plt.grid(True, alpha=0.3)
#     plt.tight_layout()
#     plt.show()


if __name__ == "__main__":
    full_df, ft_data, config = load_and_normalize_data("plot_config.yaml")
    if config["plot"]:
        plot_figure(full_df, ft_data, config)
        # plot_figure_dedup_cost(full_df, ft_data, config)
    else:
        print_avg_improvements_per_height(full_df)
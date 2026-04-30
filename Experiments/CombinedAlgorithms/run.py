import os
import glob
import yaml
import csv
import multiprocessing
import time
from timeit import default_timer as timer

from FaultTree.FTParser import FTParse
from Algorithms.Cost.BarraCuDA import BarraCuDA


# -------------------------
# Timeout wrapper
# -------------------------
def _wrapper(queue, func, args):
    result = func(*args)
    queue.put(result)


def run_with_timeout(func, args=(), timeout=60):
    queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=_wrapper, args=(queue, func, args))

    p.start()
    p.join(timeout)

    if p.is_alive():
        p.terminate()
        p.join()
        return None, True
    else:
        return queue.get(), False


# -------------------------
# Algorithm
# -------------------------
def apply_algorithm_BarraCuDA(ft, height):
    exp_cost = []
    exp_cost_failure = []
    runtime = []

    for i in range(height):
        start = timer()

        ddt = BarraCuDA(ft, i)
        if i != 0:
            ddt = ddt.remove_duplicate_vertices()

        end = timer()

        exp_cost.append(ddt.expected_cost())
        exp_cost_failure.append(
            ddt.expected_cost_failure() / ddt.fail_prob()
        )
        runtime.append(end - start)

    return exp_cost, exp_cost_failure, runtime


# -------------------------
# FT loader
# -------------------------
def load_ft(filepath):
    FaultTree = FTParse(filepath)
    FaultTree.unreliability(add_unreliability=True)
    return FaultTree


# -------------------------
# Main experiment runner
# -------------------------
def run_barracuda_experiment(cfg):
    """
    Runs BarraCuDA on all .dft files in cfg["paths"]["ft_dir"]
    and stores CSV results in cfg["paths"]["results_dir"]
    """

    ft_folder = cfg["paths"]["ft_dir"]
    output_folder = cfg["paths"]["results_dir"]
    timeout = cfg["experiment"].get("timeout", 60)
    recursive = cfg["experiment"].get("recursive", False)

    os.makedirs(output_folder, exist_ok=True)

    pattern = "**/*.dft" if recursive else "*.dft"
    ft_files = glob.glob(os.path.join(ft_folder, pattern), recursive=recursive)

    print(f"Found {len(ft_files)} fault trees.")

    for filepath in ft_files:
        print(f"Processing: {filepath}")

        try:
            ft = load_ft(filepath)
            height = ft.max_height()

            result, timed_out = run_with_timeout(
                apply_algorithm_BarraCuDA,
                args=(ft, height),
                timeout=timeout
            )

            if timed_out:
                print(f"Timed out: {filepath}")
                continue

            exp_cost, exp_cost_failure, runtime = result

            ft_name = os.path.splitext(os.path.basename(filepath))[0]
            csv_path = os.path.join(output_folder, f"{ft_name}.csv")

            with open(csv_path, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    "height",
                    "expcost",
                    "expcost_given_failure",
                    "runtime"
                ])

                for i in range(len(exp_cost)):
                    writer.writerow([
                        i,
                        exp_cost[i],
                        exp_cost_failure[i],
                        runtime[i]
                    ])

            print(f"Saved: {csv_path}")

        except Exception as e:
            print(f"Error processing {filepath}: {e}")

    print("Finished BarraCuDA experiment.")


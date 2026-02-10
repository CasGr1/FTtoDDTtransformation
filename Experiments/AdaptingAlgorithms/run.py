import os
import csv
import yaml
import multiprocessing as mp
from timeit import default_timer as timer
import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

from FaultTree.FTParser import *

# Algorithm imports
from Algorithms.Cost.EDAcost import EDAcost
from Algorithms.Cost.PaDAcost import PaDAcost
from Algorithms.Cost.BUDAcost import BUDAcost
from Algorithms.Cost.CuDAcost import CuDAcost
from Algorithms.Height.EDA import EDA
from Algorithms.Height.PaDA import PaDAprob
from Algorithms.Height.BUDA import BUDA
from Algorithms.Height.CuDA import CuDAprob

# Result constants
OOM_RESULT = "OOM"
ERROR_RESULT = "ERR"
TIMEOUT_RESULT = "TIMEOUT"

# ----------------------------
# Load YAML config
# ----------------------------
def load_config(yaml_file="run_config.yaml"):
    with open(yaml_file, "r") as f:
        return yaml.safe_load(f)

# ----------------------------
# Compute expected costs
# ----------------------------
def expected_costs_from_tree(FaultTree, algorithm, runtime_flag=False):
    B = FaultTree.variables()
    P = FaultTree.probabilities()
    cost = FaultTree.cost_dict()

    def _measure(func, runs=1):
        total = 0
        res = None
        for _ in range(runs):
            start = timer()
            res = func()
            total += timer() - start
        return res, total / runs

    def _postprocess(ddt):
        exp_cost = ddt.expected_cost()
        exp_cost_fail = ddt.expected_cost_failure() / (ddt.fail_prob() or 1)
        return exp_cost, exp_cost_fail

    runs = 25 if runtime_flag else 1

    alg_map = {
        "EDA": lambda: EDA(FaultTree, B, P, cost),
        "EDAcost": lambda: EDAcost(FaultTree, B, P, cost),
        "BUDA": lambda: BUDA(FaultTree).remove_duplicate_vertices(),
        "BUDAcost": lambda: BUDAcost(FaultTree).remove_duplicate_vertices(),
        "CuDA": lambda: CuDAprob(FaultTree, FaultTree.cut_set()),
        "CuDAcost": lambda: CuDAcost(FaultTree, FaultTree.cut_set()),
        "PaDA": lambda: PaDAprob(FaultTree, FaultTree.path_set()),
        "PaDAcost": lambda: PaDAcost(FaultTree, FaultTree.path_set()),
    }

    ddt, rtime = _measure(alg_map[algorithm], runs)
    return (*_postprocess(ddt), rtime)

# ----------------------------
# Simple file metrics
# ----------------------------
def countbes(filename):
    count = 0
    with open(filename, "r") as f:
        for line in f:
            line = line.strip().replace('"', '').replace(';', '')
            tokens = line.split()
            if len(tokens) > 1 and "prob" in tokens[1]:
                count += 1
    return count

def find_num_gates(filename):
    gates = 0
    with open(filename, "r") as f:
        for line in f:
            line = line.strip().replace('"', '').replace(';', '')
            tokens = line.split()
            if len(tokens) > 1 and ("or" in tokens[1] or "and" in tokens[1]):
                gates += 1
    return gates

# ----------------------------
# CSV header
# ----------------------------
def write_csv_header(output_folder, algname, addition):
    os.makedirs(output_folder, exist_ok=True)
    path = os.path.join(output_folder, f"{algname}{addition}.csv")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["FT", "expcost", "expcost_given_failure", "bes", "time(s)", "gates", "CS"])

def _worker(q, file_path, fname, algorithms, addition):
    try:
        results = []

        FaultTree = FTParse(file_path)
        FaultTree.unreliability(add_unreliability=True)

        bes = countbes(file_path)
        gates = find_num_gates(file_path)
        cs = len(FaultTree.cut_set())

        for alg in algorithms:
            expcost, expcost_fail, runtime = expected_costs_from_tree(
                FaultTree, alg, runtime_flag=False
            )
            results.append(
                (alg, addition, fname, expcost, expcost_fail, bes, runtime, gates, cs)
            )

        q.put(("OK", results))

    except MemoryError:
        q.put(("OOM", None))

    except Exception as e:
        q.put(("ERR", repr(e)))

    finally:
        try:
            import gc
            gc.collect()
        except Exception:
            pass

def process_file(file_path, fname, algorithms, addition, timeout=1):
    q = mp.Queue()
    p = mp.Process(
        target=_worker,
        args=(q, file_path, fname, algorithms, addition)
    )

    print(f"file starting: {file_path} at {datetime.datetime.now()}")
    p.start()
    p.join(timeout)

    if p.is_alive():
        print(f"TIMEOUT: {file_path}")
        p.terminate()
        p.join()
        return [
            (alg, addition, fname, TIMEOUT_RESULT, TIMEOUT_RESULT, 0, 0, 0, 0)
            for alg in algorithms
        ]

    if q.empty():
        print(f"NO RESULT (likely crash): {file_path}")
        return [
            (alg, addition, fname, ERROR_RESULT, ERROR_RESULT, 0, 0, 0, 0)
            for alg in algorithms
        ]

    status, payload = q.get()

    if status == "OOM":
        print(f"OUT OF MEMORY: {file_path}")
        return [
            (alg, addition, fname, OOM_RESULT, OOM_RESULT, 0, 0, 0, 0)
            for alg in algorithms
        ]

    if status == "ERR":
        print(f"ERROR in worker ({payload}): {file_path}")
        return [
            (alg, addition, fname, ERROR_RESULT, ERROR_RESULT, 0, 0, 0, 0)
            for alg in algorithms
        ]

    print(f"file done: {file_path}")
    return payload

# ----------------------------
# Main execution
# ----------------------------
if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)  # Windows safe

    config = load_config("run_config.yaml")
    folder = config["folder"]
    output_folder = config["output_folder"]
    addition = config.get("addition", "TEST")
    algorithms = config.get("algorithms", ["BUDAcost", "BUDA"])
    timeout_sec = config.get("timeout", 10)
    runtime_flag = config.get("runtime", True)
    max_workers = config.get("max_workers") or max(1, os.cpu_count() // 2)
    with_subfolder = config.get("with_subfolder", False)

    # Prepare CSV files
    for alg in algorithms:
        write_csv_header(output_folder, alg, addition)

    # Prepare tasks
    tasks = []
    if with_subfolder:
        for sup in os.listdir(folder):
            supfolder = os.path.join(folder, sup)
            if not os.path.isdir(supfolder):
                continue
            for fname in os.listdir(supfolder):
                full_path = os.path.join(supfolder, fname)
                if os.path.isfile(full_path):
                    tasks.append((full_path, os.path.join(sup, fname)))
    else:
        for fname in os.listdir(folder):
            full_path = os.path.join(folder, fname)
            if os.path.isfile(full_path):
                tasks.append((full_path, fname))

    MAX_WORKERS = max(1, os.cpu_count() // 2)

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_file, *task, algorithms, addition, timeout_sec) for task in tasks]

        try:
            for future in as_completed(futures):
                results = future.result()

                for (
                        alg,
                        addition,
                        fname,
                        expcost,
                        expcost_fail,
                        bes,
                        runtime,
                        gates,
                        cs
                ) in results:
                    csv_path = os.path.join(output_folder, f"{alg}{addition}.csv")
                    with open(csv_path, "a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            fname,
                            expcost,
                            expcost_fail,
                            bes,
                            runtime,
                            gates,
                            cs
                        ])
                        f.flush()

        except KeyboardInterrupt:
            print("\nInterrupted! Writing completed results and shutting down...")
            executor.shutdown(wait=False, cancel_futures=True)
            raise

import numpy as np

from Experiments.CombinedAlgorithms.run import run_with_timeout, apply_algorithm_BarraCuDA
from FaultTree.FT_random_generator import FaultTreeGenerator, save_ft
from FaultTree.FTintoDAG import *
from FaultTree.FTadapt import convert_all_fault_trees
from Experiments.AdaptingAlgorithms.run import run_experiments
from Experiments.AdaptingAlgorithms.plot import run_plots
from Experiments.WorstCase.Run_WorstCase import plot_accuracy_vs_threshold
from Experiments.CombinedAlgorithms.run import run_barracuda_experiment
from Experiments.CombinedAlgorithms.plot import run_plots_from_cfg
import os
import yaml

def load_config(config_path: str):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def clean_folder(folder_path: str):
    """
    Deletes all files/subfolders in a directory safely.
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        return

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)

        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        except Exception as e:
            print(f"Could not delete {item_path}: {e}")

def generate_fts(cfg):
    ft_paths = []

    exp_cfg = cfg["experiment"]
    gen_cfg = cfg.get("ft_generation", {})
    path_cfg = cfg["paths"]

    be_start, be_end = gen_cfg["be_range"]
    n_per_size = gen_cfg["n_per_size"]

    or_range = gen_cfg.get("or_prob_range", [0.0, 1.0])
    maxc_range = gen_cfg.get("max_children_range", [2, 10])

    ft_dir = os.path.join(path_cfg["base_dir"], "fts")
    os.makedirs(ft_dir, exist_ok=True)

    for be in range(be_start, be_end):
        for i in range(1, n_per_size + 1):

            or_p = np.random.uniform(*or_range)
            max_children = np.random.randint(*maxc_range)

            gen = FaultTreeGenerator(or_prob=or_p)
            ft = gen.generate_FT(be, max_children=max_children)

            filename = f"be{be}_ft{i}_orp{or_p:.2f}_mc{max_children}.dft"
            path = os.path.join(ft_dir, filename)

            save_ft(ft, path)
            ft_paths.append(path)

    return ft_paths

def run_exp1(cfg):
    print(f"Running experiment: {cfg['experiment'].get('name', 'unnamed')}")

    if "seed" in cfg:
        np.random.seed(cfg["seed"])

    # Step 1: Generate FTs
    if cfg["experiment"]["gen_ft"]:
        print("Generating fault trees...")
        ft_cfg = cfg["ft_generation"]

        base_dir = cfg["paths"]["base_dir"]
        ft_dir = os.path.join(base_dir, ft_cfg.get("output_subdir", "FTs"))

        if ft_cfg.get("clean_output", False):
            print(f"Cleaning FT folder: {ft_dir}")
            clean_folder(ft_dir)

        ft_paths = generate_fts(cfg)

        # Step 2: Optional DAG transformation
        if cfg.get("dag", {}).get("enabled", False):
            print("Transforming FTs into DAGs...")

            dag_cfg = cfg["dag"]
            dag_paths = []
            base_dir = cfg["paths"]["base_dir"]
            dag_dir = os.path.join(base_dir, cfg["dag"].get("output_subdir", "dags"))

            if dag_cfg.get("clean_output", False):
                print(f"Cleaning DAG folder: {dag_dir}")
                clean_folder(dag_dir)

            for ft_path in ft_paths:
                filename = os.path.basename(ft_path)
                out_path = os.path.join(dag_dir, filename)

                dag_path = transform_to_dag(ft_path, out_path, cfg["dag"])
                dag_paths.append(dag_path)

            ft_paths = dag_paths  # overwrite → downstream uses DAGs

    # Step 3: Run algorithms
    print("Running algorithms...")
    results = run_experiments(cfg)

    # Step 4: Plot
    if cfg.get("plot", {}).get("enabled", True):
        print("Plotting results...")
        run_plots(cfg)


def run_exp2(cfg):
    print("Run worst case experiment")

    exp_cfg = cfg["experiment"]
    path_cfg = cfg["paths"]

    if exp_cfg["gen_ft"]:
        clean_folder(path_cfg["ft_folder"])
        clean_folder(path_cfg["binary_folder"])
        # ----------------------------
        # Step 1: Generate Fault Trees
        # ----------------------------
        if exp_cfg.get("gen_ft", True):
            print("Generating fault trees...")
            ft_paths = generate_fts(cfg)
        else:
            ft_paths = path_cfg["ft_folder"]

        # ----------------------------
        # Step 2: Convert to Binary FT (PER FILE, not whole folder)
        # ----------------------------

        convert_all_fault_trees(
            input_folder=path_cfg["ft_folder"],
            output_folder=path_cfg["binary_folder"]
        )

    # ----------------------------
    # Step 3: Run algorithms
    # ----------------------------
    print("Running BUDA + Worst-case algorithms...")

    cfg["experiment"]["algorithms"] = [
        "BUDA",
        "BUDAcost",
    ]

    results = run_experiments(cfg)

    # ----------------------------
    # Step 4: Worst-case analysis (NO plotting inside function)
    # ----------------------------
    print("Computing worst-case accuracy vs threshold...")

    best_threshold, best_accuracy = plot_accuracy_vs_threshold(
        config=cfg["plot_folder"],
        metric=cfg["accuracyorprecision"],
        min_threshold=1.0,
        max_threshold=2.0,
        step=0.01
    )

def run_exp3(cfg):
    print("Running experiment: exp3 (combined fault trees)")
    if cfg["experiment"]["ft_gen"]:
        if "seed" in cfg:
            import numpy as np
            np.random.seed(cfg["seed"])

        if cfg["experiment"]["clean_dir"]:
            print(f"Cleaning DAG folder: {cfg["paths"]["ft_dir"]}")
            clean_folder(cfg["paths"]["ft_dir"])

        exp_cfg = cfg["experiment"]
        path_cfg = cfg["paths"]

        base_folder = exp_cfg["base_ft_folder"]
        output_folder = os.path.join(path_cfg["base_dir"], "exp3_results")
        ft_output_folder = os.path.join(path_cfg["base_dir"], "exp3_fts")

        os.makedirs(output_folder, exist_ok=True)
        os.makedirs(ft_output_folder, exist_ok=True)

        n_samples = exp_cfg.get("n_samples", 20)
        min_size = exp_cfg.get("min_size", 7)
        timeout = exp_cfg.get("timeout", 60)

        for i in range(n_samples):
            print(f"\nGenerating combined FT {i}")

            # -------------------------
            # Step 1: Generate combined FT
            # -------------------------
            out_path = os.path.join(ft_output_folder, f"temp_{i}.dft")

            ft = random_gen(base_folder, min_size, out_path)

            # random_gen already saves temp; re-save properly
            FTsave(ft[0], ft[1], out_path)
    clean_folder(cfg["paths"]["results_dir"])
    run_barracuda_experiment(cfg)

    run_plots_from_cfg(cfg)


def run_pipeline(cfg):
    exp_type = cfg["experiment"]["type"]

    print(f"Running experiment type: {exp_type}")

    if exp_type == "exp1":
        run_exp1(cfg)
    elif exp_type == "exp2":
        run_exp2(cfg)
    elif exp_type == "exp3":
        run_exp3(cfg)
    else:
        raise ValueError(f"Unknown experiment type: {exp_type}")

def main(config_path):
    config = load_config(config_path)
    run_pipeline(config)


if __name__ == "__main__":
    config_file = "configs/exp3.yaml"
    main(config_file)
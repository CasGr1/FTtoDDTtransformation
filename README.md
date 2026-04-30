# README

## Running Experiments

The `main.py` file is the entry point for running all experiments in this project. By adapting which config file is referenced, different experiments can be run.

You can use it to execute the following experiments:

### Experiment 1 – Adapted Algorithms

This experiment evaluates the performance of the adapted algorithms.

Two configuration files are available:

* **`config/exp1.yaml`**
  Generates fault trees from scratch and runs the algorithms on these generated instances.

* **`config/thesis/exp1.yaml`**
  Reproduces the results from the thesis by running the algorithms on the predefined fault trees used.


### Experiment 2 – Worst Case Scenario
  This experiment runs both BUDAcost and BUDA to determine the measure ratio, then calculates the worst case ratio from the worstratio algorithm. Finally it plots the precision or accuracy vs threshold T.

* **`config/exp2.yaml`**
  Generates fault trees from scratch, transform these FTs into binary FTs. Then it runs the algorithms on these generated instances and calculates the worst case ratio.

* **`config/thesis/exp2.yaml`**
  Reproduces the results from the thesis by running the algorithms on the predefined fault trees used.

### Experiment 3 – Combined Algorithm
  This experiment runs the BarraCuDA algorithm.
* **`config/exp3.yaml`**
  Combines FTs from the FFORT benchmark until they reach the minimum depth. Then it runs the BarraCuDA algorithms on these generated instances and plots the normalised runtime vs the normalised expected cost.

* **`config/thesi3/exp2.yaml`**
  Reproduces the results from the thesis by running the algorithms on the predefined fault trees used.

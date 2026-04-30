import random
from .FTcombine import *
from .FaultTree import *
import re

def merge_two_bes(bes, gates):
    if len(bes) < 2:
        return bes, gates

    i, j = random.sample(range(len(bes)), 2)

    keep_be = bes[i][0]
    remove_be = bes[j][0]

    for gate in gates:
        for k in range(len(gate)):
            if gate[k] == remove_be:
                gate[k] = keep_be

    bes.pop(j)

    return bes, gates

def extract_gate_number(gate_name):
    match = re.search(r'\d+', gate_name)
    return int(match.group()) if match else None


def replace_be_with_gate(bes, gates):
    if not bes:
        return bes, gates

    be_index = random.randint(0, len(bes) - 1)
    old_be = bes[be_index][0]

    top_gate = "G1"

    parent_gates = []
    for gate in gates:
        if old_be in gate[1:]:
            parent_gates.append(gate[0])

    if not parent_gates:
        return bes, gates

    parent_numbers = [
        extract_gate_number(pg) for pg in parent_gates
        if extract_gate_number(pg) is not None
    ]

    if not parent_numbers:
        return bes, gates

    min_parent_number = min(parent_numbers)

    candidate_gates = []
    for g in gates:
        gate_name = g[0]
        gate_number = extract_gate_number(gate_name)

        if (
            gate_name != top_gate
            and gate_name != old_be
            and gate_number is not None
            and gate_number > min_parent_number
        ):
            candidate_gates.append(gate_name)

    if not candidate_gates:
        return bes, gates

    new_gate = random.choice(candidate_gates)

    for gate in gates:
        for i in range(1, len(gate)):
            if gate[i] == old_be:
                gate[i] = new_gate

    bes.pop(be_index)

    return bes, gates

import os
import shutil


def clear_folder(folder_path):
    if not os.path.exists(folder_path):
        return

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")

def transform_to_dag(ft_path, output_path, cfg):
    gates, bes = FTpartialparser(ft_path, None)

    dag_prob = np.random.rand()
    be_prob = np.random.rand()

    if dag_prob < cfg.get("replace_be_prob", 0.1):
        bes, gates = replace_be_with_gate(bes, gates)

    for _ in range(int(len(bes) / 10)):
        if be_prob < cfg.get("merge_be_prob", 0.2):
            bes, gates = merge_two_bes(bes, gates)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    FTsave(gates, bes, output_path)

    return output_path

if __name__ == "__main__":
    folder_in = "FTs/FTFINAL/NORMAL"
    folder_out = "FTs/FTFINAL/DAG"
    for file in os.listdir(folder_in):
        # ft = FTParse(os.path.join(folder_out, file))
        # print(ft.shape())
        filename = os.path.join(folder_in, file)
        gates, bes = FTpartialparser(filename, None)
        print(bes)
        dag_prob = np.random.rand()
        be_prob = np.random.rand()
        if dag_prob < 0.1:
            replace_be_with_gate(bes, gates)
        for i in range(int(len(bes)/10)):
            print(i)
            if be_prob < 0.2:
                merge_two_bes(bes, gates)
        # FTsave(gates, bes, os.path.join(folder_out, file))


import random
from FTcombine import *
from FaultTree import *
import re

def merge_two_bes(bes, gates):
    if len(bes) < 2:
        return bes, gates  # Not enough BEs to modify

    # Pick two distinct indices randomly
    i, j = random.sample(range(len(bes)), 2)

    # Decide which BE stays and which is removed
    keep_be = bes[i][0]
    remove_be = bes[j][0]

    # Update gates: replace all references to removed BE with kept BE
    for gate in gates:
        for k in range(len(gate)):
            if gate[k] == remove_be:
                gate[k] = keep_be

    # Remove the redundant BE
    bes.pop(j)

    return bes, gates

def extract_gate_number(gate_name):
    """
    Extract numeric part from gate name like 'G12' -> 12
    Returns None if no number found.
    """
    match = re.search(r'\d+', gate_name)
    return int(match.group()) if match else None


def replace_be_with_gate(bes, gates):
    if not bes:
        return bes, gates

    # Pick a random BE
    be_index = random.randint(0, len(bes) - 1)
    old_be = bes[be_index][0]

    top_gate = "G1"

    # Find all parent gates where this BE appears
    parent_gates = []
    for gate in gates:
        if old_be in gate[1:]:  # skip gate[0], which is the gate name itself
            parent_gates.append(gate[0])

    if not parent_gates:
        return bes, gates  # No parents found

    # Get the smallest parent gate number (strictest constraint)
    parent_numbers = [
        extract_gate_number(pg) for pg in parent_gates
        if extract_gate_number(pg) is not None
    ]

    if not parent_numbers:
        return bes, gates

    min_parent_number = min(parent_numbers)

    # Candidate gates must:
    # - Not be the top gate
    # - Not be the BE itself
    # - Have a higher gate number than parent
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
        return bes, gates  # No valid replacement

    # Pick a valid replacement gate
    new_gate = random.choice(candidate_gates)

    # Replace BE references with chosen gate
    for gate in gates:
        for i in range(1, len(gate)):  # skip gate name
            if gate[i] == old_be:
                gate[i] = new_gate

    # Remove BE from BE list
    bes.pop(be_index)

    return bes, gates

# def replace_be_with_gate(bes, gates):
#     # Pick a random BE
#     be_index = random.randint(0, len(bes) - 1)
#     old_be = bes[be_index][0]
#
#     top_gate = "G1"
#     candidate_gates = [g[0] for g in gates if g[0] != top_gate and g[0] != old_be]
#
#     if not candidate_gates:
#         # No valid gate to replace with
#         return bes, gates
#
#     # Pick a random gate from candidates
#     new_gate = random.choice(candidate_gates)
#
#     # Update all gates: replace references to the BE with the chosen gate
#     for gate in gates:
#         for i in range(len(gate)):
#             if gate[i] == old_be:
#                 gate[i] = new_gate
#
#     # Remove the BE from the BE list
#     bes.pop(be_index)
#
#     return bes, gates

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
        FTsave(gates, bes, os.path.join(folder_out, file))


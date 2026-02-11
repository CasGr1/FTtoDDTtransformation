import random
from FTcombine import *
from FaultTree import *

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

def replace_be_with_gate(bes, gates):
    # Pick a random BE
    be_index = random.randint(0, len(bes) - 1)
    old_be = bes[be_index][0]

    top_gate = "G1"
    candidate_gates = [g[0] for g in gates if g[0] != top_gate and g[0] != old_be]

    if not candidate_gates:
        # No valid gate to replace with
        return bes, gates

    # Pick a random gate from candidates
    new_gate = random.choice(candidate_gates)

    # Update all gates: replace references to the BE with the chosen gate
    for gate in gates:
        for i in range(len(gate)):
            if gate[i] == old_be:
                gate[i] = new_gate

    # Remove the BE from the BE list
    bes.pop(be_index)

    return bes, gates

if __name__ == "__main__":
    folder_in = "FTs/RandomGen/Benchmark/"
    folder_out = "FTs/RandomGen/BenchmarkDAG/"
    for file in os.listdir(folder_in):
        # ft = FTParse(os.path.join(folder_out, file))
        # print(ft.shape())
        filename = os.path.join(folder_in, file)
        gates, bes = FTpartialparser(filename, None)
        dag_prob = np.random.rand()
        be_prob = np.random.rand()
        if dag_prob < 0.1:
            replace_be_with_gate(bes, gates)
        for i in range(int(len(bes)/10)):
            print(i)
            if be_prob < 0.2:
                merge_two_bes(bes, gates)
        FTsave(gates, bes, os.path.join(folder_out, file))


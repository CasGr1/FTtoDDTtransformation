from FaultTree import *
import numpy as np


class FaultTreeGenerator:
    def __init__(self, or_prob=0.5):
        self.counters = {"BE": 0, "G": 0}
        self.or_prob = or_prob

    def generate_FT(self, be_budget, max_children=4):
        # ----- BASIC EVENT -----
        if be_budget == 1:
            self.counters["BE"] += 1
            prob = np.clip(np.random.uniform(0.00001, 0.01), 0, 1)
            cost = np.random.randint(1, 11)
            return FT(
                f"BE{self.counters['BE']}",
                FtElementType.BE,
                prob=prob,
                cost=cost
            )

        # ----- GATE -----
        gate_type = FtElementType.OR if np.random.rand() < self.or_prob else FtElementType.AND
        self.counters["G"] += 1
        gate_name = f"G{self.counters['G']}"

        # Create gate node first with empty children
        node = FT(name=gate_name, ftelement=gate_type, children=[])

        # Determine number of children
        max_k = min(max_children, be_budget)
        n_children = np.random.randint(2, max_k + 1)

        # Split budget among children
        splits = np.ones(n_children, dtype=int)
        remaining = be_budget - n_children
        for _ in range(remaining):
            splits[np.random.randint(0, n_children)] += 1

        # Recursively generate children and attach to gate
        for b in splits:
            child = self.generate_FT(b, max_children)
            node.children.append(child)

        return node



def save_ft(ft, output):
    new_lines = [f"toplevel \"{ft.name}\";"]

    visited = set()

    gate_lines = []
    be_lines = []

    def visit(node):
        if id(node) in visited:
            return
        visited.add(id(node))

        # ----- BASIC EVENT -----
        if node.type == FtElementType.BE:
            be_lines.append(
                f"\"{node.name}\" prob={node.prob:.3e} cost={node.cost};"
            )
            return

        # ----- GATE -----
        gate_type = (
            "and" if node.type == FtElementType.AND else "or"
        )

        children_names = " ".join(f"\"{c.name}\"" for c in node.children)

        gate_lines.append(
            f"\"{node.name}\" {gate_type} {children_names};"
        )

        for child in node.children:
            visit(child)
    visit(ft)
    new_lines.extend(gate_lines)
    new_lines.extend(be_lines)

    with open(output, "w") as f:
        f.write("\n".join(new_lines))


if __name__ == "__main__":
    for i in range(1,10):
        or_p = np.random.uniform(0, 1)
        gen = FaultTreeGenerator(or_prob=or_p)
        bes = np.random.randint(2,50)
        FaultT = gen.generate_FT(bes, max_children=2)

        save_ft(FaultT, f"FTs/RandomGen/Benchmark/ft{i}_bes{bes}_or{round(or_p, 3)}.dft")
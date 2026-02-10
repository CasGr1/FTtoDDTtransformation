from FaultTree import *
import numpy as np


class FaultTreeGenerator:
    def __init__(self, or_prob=0.5):
        self.counters = {"BE": 0, "G": 0}
        self.node_pool = []
        self.or_prob = or_prob

    def generate_FT(self, be_budget, max_children=4):
        reuse = np.random.rand()

        if be_budget == 1:
            self.counters["BE"] += 1
            node = FT(
                f"BE{self.counters['BE']}",
                FtElementType.BE,
                prob=np.random.uniform(0, 10) * (10 ** np.random.uniform(-5, -3)),
                cost=round(np.random.geometric(0.01))
            )
            return node

        gate = np.random.choice(["AND", "OR"], p=[1 - self.or_prob, self.or_prob])
        self.counters["G"] += 1

        max_k = min(max_children, be_budget)
        n_children = np.random.randint(2, max_k + 1)

        splits = np.ones(n_children, dtype=int)
        remaining = be_budget - n_children
        for _ in range(remaining):
            splits[np.random.randint(0, n_children)] += 1

        children = [self.generate_FT(b, max_children) for b in splits]

        node = FT(
            name=f"G{self.counters['G']}",
            ftelement=FtElementType.AND if gate == "AND" else FtElementType.OR,
            children=children
        )

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
    for i in range(1,500):
        or_p = np.random.uniform(0, 1)
        gen = FaultTreeGenerator(or_prob=or_p)
        bes = np.random.randint(2,50)
        FaultT = gen.generate_FT(bes, max_children=2)

        save_ft(FaultT, f"FTs/RandomGen/Benchmark/ft{i}_bes{bes}_or{round(or_p, 3)}.dft")
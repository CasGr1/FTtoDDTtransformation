from FaultTree.FaultTree import *
from DDT.DDT import *


def BUDAcost(ft, no_dag=False):
    ddt = BUDAcostalgorithm(ft)
    if not no_dag:
        return ddt.remove_duplicate_vertices()
    if no_dag:
        return ddt


def BUDAcostalgorithm(ft):
    # Base case: Basic Event (leaf)
    if ft.type == FtElementType.BE:
        return DDT(
            name=ft.name,
            ddtelement=DdtElementType.DEC,
            children=[
                DDT('ZERO', DdtElementType.ZERO),
                DDT('ONE', DdtElementType.ONE)
            ],
            prob=ft.prob,
            cost=ft.cost
        )

    subtrees = [BUDAcostalgorithm(ch) for ch in ft.children]

    if ft.type == FtElementType.AND:
        ordered_children = sorted(subtrees, key=lambda x: x.expected_cost()/(1-x.fail_prob()))
        new_ddt = ordered_children[0]
        for i in range(1,len(ordered_children)):
            new_ddt = replace_leaves(new_ddt, DdtElementType.ONE, ordered_children[i])
        return new_ddt

    elif ft.type == FtElementType.OR:
        ordered_children = sorted(subtrees, key=lambda x: x.expected_cost()/x.fail_prob())
        new_ddt = ordered_children[0]
        for i in range(1, len(ordered_children)):
            new_ddt = replace_leaves(new_ddt, DdtElementType.ZERO, ordered_children[i])
        return new_ddt


def replace_leaves(ddt, target_type, replacement):
    # If current node is a leaf of the target type, replace it
    if ddt.type == target_type:
        return replacement

    # If DEC node, recurse on children
    if ddt.type == DdtElementType.DEC:
        new_children = [replace_leaves(child, target_type, replacement) for child in ddt.children]
        return DDT(
            name=ddt.name,
            ddtelement=DdtElementType.DEC,
            children=new_children,
            prob=ddt.prob,
            cost=ddt.cost
        )

    # Other leaves (not target) stay the same
    return ddt
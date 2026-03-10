from FaultTree.FaultTree import *
from Algorithms.Cost.CuDAcost import *
from DDT.DDT import *


def BarraCuDA(ft, BUDADEPTH, depth=0):
    ddt = BarraCuDA_algorithm(ft, BUDADEPTH, depth)
    return ddt.remove_duplicate_vertices()


def BarraCuDA_algorithm(ft, BUDADEPTH, depth=0):
    """
    This is an algorithm for transforming fault trees to diagnostic decision trees using a bottom-up approach
    :param ft: the fault tree that needs to be performed
    :return: diagnostic decision tree
    """
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

    if depth < BUDADEPTH:
        subtrees  = [BarraCuDA(ch, BUDADEPTH, depth+1) for ch in ft.children]
        if ft.type == FtElementType.AND:
            ordered_children = sorted(subtrees, key=lambda x: x.expected_cost() / (1 - x.fail_prob()))
            new_ddt = ordered_children[0]
            for i in range(1, len(ordered_children)):
                new_ddt = replace_leaves(new_ddt, DdtElementType.ONE, ordered_children[i])
            return new_ddt

        if ft.type == FtElementType.OR:
            ordered_children = sorted(subtrees, key=lambda x: x.expected_cost()/x.fail_prob())
            new_ddt = ordered_children[0]
            for i in range(1, len(ordered_children)):
                new_ddt = replace_leaves(new_ddt, DdtElementType.ZERO, ordered_children[i])
            return new_ddt

    else:
        cutsets = ft.cut_set()
        ddt = CuDAcost(ft, cutsets)
        return ddt

def replace_leaves(ddt, target_type, replacement):
    if ddt.type == target_type:
        return replacement

    if ddt.type == DdtElementType.DEC:
        new_children = [replace_leaves(child, target_type, replacement) for child in ddt.children]
        return DDT(
            name=ddt.name,
            ddtelement=DdtElementType.DEC,
            children=new_children,
            prob=ddt.prob,
            cost=ddt.cost
        )

    return ddt


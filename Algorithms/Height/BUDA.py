from FaultTree.FaultTree import *
from DDT.DDT import *


def BUDA(ft):
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
        )
    if ft.type == FtElementType.AND:
        ordered_children = sorted(ft.children, key=lambda child: child.prob)
        new_ddt = ordered_children[0]
        for i in range(1, len(ordered_children)):
            new_ddt = replace_leaves(new_ddt, DdtElementType.ONE, ordered_children[i])
        return new_ddt
    if ft.type == FtElementType.OR:
        ordered_children = sorted(ft.children, key=lambda child: child.prob, reverse=True)
        new_ddt = ordered_children[0]
        for i in range(1, len(ordered_children)):
            new_ddt = replace_leaves(new_ddt, DdtElementType.ONE, ordered_children[i])
        return new_ddt


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
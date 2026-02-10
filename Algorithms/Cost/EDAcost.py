from FaultTree.FaultTree import *
from DDT.DDT import *


def EDAcost(ft, variables, probabilities, cost):
    if ft_false(ft):
        return DDT('ZERO', DdtElementType.ZERO)
    if ft_true(ft):
        return DDT('ONE', DdtElementType.ONE)

    optimal_cost = float('inf')
    optimal_ddt = None

    for var in variables:
        remaining_var = variables - {var}
        left_ft = restrict(ft, var, 0)
        right_ft = restrict(ft, var, 1)

        left_ddt = EDAcost(left_ft, remaining_var, probabilities, cost)
        right_ddt = EDAcost(right_ft, remaining_var, probabilities, cost)

        expected_cost = cost[var] + (1-probabilities[var])*left_ddt.expected_cost() + probabilities[var]*right_ddt.expected_cost()

        if expected_cost < optimal_cost:
            optimal_cost = expected_cost
            optimal_ddt = DDT(name=var, ddtelement=DdtElementType.DEC, children=[left_ddt, right_ddt], prob=probabilities[var], cost=cost[var])
    return optimal_ddt


def restrict(ft, var, value):
    if ft.type == FtElementType.BE:
        if ft.name == var:
            return FT(ft.name, FtElementType.BE, prob=value)
        else:
            return ft

    new_children = [restrict(child, var, value) for child in ft.children]

    if all(child.type == FtElementType.BE and child.probabilities in [0, 1] for child in new_children):
        if ft.type == FtElementType.AND:
            if any(child.prob == '0' for child in new_children):
                return FT('ZERO', FtElementType.BE, prob=0)
            else:
                return FT('ONE', FtElementType.BE, prob=1)
        elif ft.type == FtElementType.OR:
            if any(child.prob == 1 for child in new_children):
                return FT('ONE', FtElementType.BE, prob=1)
            else:
                return FT('ZERO', FtElementType.BE, prob=0)

    return FT(ft.name, ft.type, new_children)

def ft_false(ft):
    """
    function that checks if all elements evaluate to non-failure
    :param ft: fault tree
    :return:
    True if fault tree evaluates to 0
    False if fault tree does not evaluate to 0
    """
    if ft.type == FtElementType.BE:
        return ft.prob == 0
    if ft.type == FtElementType.AND:
        return any(ft_false(child) for child in ft.children)
    if ft.type == FtElementType.OR:
        return all(ft_false(child) for child in ft.children)

def ft_true(ft):
    """
    function that checks if all elements evaluate to failure
    :param ft: fault tree
    :return:
    True if fault tree evaluates to 1
    False if fault tree does not evaluate to 1
    """
    if ft.type == FtElementType.BE:
        return ft.prob == 1
    if ft.type == FtElementType.AND:
        return all(ft_true(child) for child in ft.children)
    if ft.type == FtElementType.OR:
        return any(ft_true(child) for child in ft.children)






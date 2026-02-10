from DDT.DDT import *


def CuDAcost(ft, cutsets):
    """
    This is an algorithm that transforms fault trees into diagnostic decision trees using cut sets
    :param ft: fault tree that will be converted
    :param cutsets: a set of all minimal cut sets
    :return: a diagnostic decision tree corresponding to ft
    """
    if not cutsets:
        return DDT('ZERO', DdtElementType.ZERO)
    if [] in cutsets:
        return DDT('ONE', DdtElementType.ONE)
    else:
        current_cs = find_likely_cut_set(ft, cutsets)
        var = find_min_var(ft, current_cs)
        ftvar = ft.find_vertex_by_name(var)
        return DDT(var, ddtelement=DdtElementType.DEC, children=[CuDAcost(ft, remove_cs(cutsets, var)), CuDAcost(ft, remove_var(cutsets, var))], prob=ftvar.prob, cost=ftvar.cost)


def remove_var(cutsets, remove):
    """
    This function removes all variables equal to remove argument in the set of all cut sets
    :param cutsets: set of cut sets
    :param remove: basic event that needs to be removed
    :return: set of cut sets where all basic events equal to remove are removed
    """
    updated_cutsets = [
        [e for e in cutset if e != remove]
        for cutset in cutsets
    ]
    return updated_cutsets


def remove_cs(cutsets, event):
    """
    This function removes all cut sets that contain the given event
    :param cutsets: set of cut sets
    :param event: event for which cut sets need to be removed
    :return: set of cut sets that do not contain event
    """
    updated_cutsets = [cutset for cutset in cutsets if event not in cutset]
    return updated_cutsets


def find_min_var(ft, current_cs):
    """
    This function finds the optimal variable in a cut set to test
    :param ft: fault tree that is being used
    :param current_cs: the cut set that is currently being used
    :return: variable with the highest failure probability
    """
    prob = float('inf')
    min_var = None
    for var in current_cs:
        current = ft.find_vertex_by_name(var)
        if current.cost/(1-current.prob) < prob:
            prob = current.cost/(1-current.prob)
            min_var = current.name
    return min_var


def find_likely_cut_set(ft, cutsets):
    """
    Function that calculates probability and cost of all cut set and return the optimal one
    :param ft: fault tree
    :param cutsets: set of cut sets
    :return: cut set in S with the lowest C/P ratio
    """
    max = float('inf')

    cutset = None
    for cs in cutsets:
        P = 1
        C = 0
        for vertex in cs:
            current = ft.find_vertex_by_name(vertex)
            P *= current.prob
            C += current.cost
        comp = C/P
        if comp < max:
            max = comp
            cutset = cs
    return cutset
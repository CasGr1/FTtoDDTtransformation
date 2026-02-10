from FaultTree.FaultTree import *
from DDT.DDT import *

def CuDAprob(ft, cutsets):
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
        return DDT(var, ddtelement=DdtElementType.DEC, children=[CuDAprob(ft, remove_cs(cutsets, var)), CuDAprob(ft, remove_var(cutsets, var))], prob=ftvar.prob, cost=ftvar.cost)


def CuDAsize(ft, cutsets):
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
        current_cs = sorted(cutsets, key=len)[0]
        var = find_min_var(ft, current_cs)
        ftvar = ft.find_vertex_by_name(var)
        return DDT(var, ddtelement=DdtElementType.DEC,
                   children=[CuDAprob(ft, remove_cs(cutsets, var)), CuDAprob(ft, remove_var(cutsets, var))],
                   prob=ftvar.prob, cost=ftvar.cost)


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
    Function to find the event with the highest probability within a cut set
    :param ft: fault tree that is being used
    :param current_cs: the cut set that is currently being used
    :return: variable with the highest failure probability
    """
    prob = float('inf')
    min_var = None
    for var in current_cs:
        current = ft.find_vertex_by_name(var)
        if current.prob < prob:
            prob = current.prob
            min_var = current.name
    return min_var


def find_likely_cut_set(ft, cutsets):
    """
    Function that calculates probability of all cut sets and returns the one with the highest probability
    :param ft: fault tree
    :param cutsets: set of cut sets
    :return: cut set in S with the highest probability
    """
    maxP = 0
    cutset = None
    for cs in cutsets:
        P = 1
        for vertex in cs:
            current = ft.find_vertex_by_name(vertex)
            P *= current.prob
        if P > maxP:
            maxP = P
            cutset = cs
    return cutset



from DDT.DDT import *


def PaDAprob(ft, pathsets):
    if not pathsets:
        return DDT('ONE', DdtElementType.ONE)
    if [] in pathsets:
        return DDT('ZERO', DdtElementType.ZERO)
    else:
        current_ps = find_max_path_set(ft, pathsets)
        var = find_max_var(ft, current_ps)
        ftvar = ft.find_vertex_by_name(var)
        return DDT(var, ddtelement=DdtElementType.DEC,
                   children=[PaDAprob(ft, remove_ps(pathsets, var)), PaDAprob(ft, remove_var(pathsets, var))],
                   prob=ftvar.prob, cost=ftvar.cost)


def PaDAsize(ft, pathsets):
    if not pathsets:
        return DDT('ONE', DdtElementType.ONE)
    if [] in pathsets:
        return DDT('ZERO', DdtElementType.ZERO)
    else:
        current_ps = sorted(pathsets, key=len)[0]
        var = find_max_var(ft, current_ps)
        ftvar = ft.find_vertex_by_name(var)
        return DDT(var, ddtelement=DdtElementType.DEC,
                   children=[PaDAsize(ft, remove_ps(pathsets, var)), PaDAsize(ft, remove_var(pathsets, var))],
                   prob=ftvar.prob, cost=ftvar.cost)


def remove_var(pathsets, remove):
    updated_pathsets = [
        [e for e in pathset if e != remove]
        for pathset in pathsets
    ]
    return updated_pathsets


def remove_ps(pathsets, event):
    updated_pathsets = [pathset for pathset in pathsets if event not in pathset]
    return updated_pathsets


def find_max_var(ft, current_ps):
    prob = 0
    max_var = None
    for var in current_ps:
        current = ft.find_vertex_by_name(var)
        if current.prob > prob:
            prob = current.prob
            max_var = current.name
    return max_var


def find_max_path_set(ft, pathsets):
    """
    Function that calculates probability of all path sets and returns the one with the lowest probability
    :param ft: fault tree
    :param S: set of cut sets
    :return: path set in S with the lowest probability
    """
    maxP = 0
    pathset = None
    for ps in pathsets:
        P = 1
        for vertex in ps:
            current = ft.find_vertex_by_name(vertex)
            P *= (1-current.prob)
        if P > maxP:
            maxP = P
            pathset = ps
    return pathset
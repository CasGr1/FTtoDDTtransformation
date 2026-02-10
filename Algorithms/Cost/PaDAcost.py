from DDT.DDT import *


def PaDAcost(ft, pathsets):
    if not pathsets:
        return DDT('ONE', DdtElementType.ONE)
    if [] in pathsets:
        return DDT('ZERO', DdtElementType.ZERO)
    else:
        current_ps = find_min_path_set(ft, pathsets)
        var = find_max_var(ft, current_ps)
        return var, PaDAcost(ft, remove_var(pathsets, var)), PaDAcost(ft, remove_ps(pathsets, var))


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
    prob = float('inf')
    max_var = None
    for var in current_ps:
        current = ft.find_vertex_by_name(var)
        if current.cost/(current.prob) < prob:
            prob = current.cost/(current.prob)
            max_var = current.name
    return max_var


def find_min_path_set(ft, pathsets):
    maxP = float('inf')
    pathset = None
    for ps in pathsets:
        P = 1
        C = 0
        for vertex in ps:
            current = ft.find_vertex_by_name(vertex)
            P *= (1-current.prob)
            C += current.cost
        comp = C/P
        if comp < maxP:
            maxP = P
            pathset = ps
    return pathset
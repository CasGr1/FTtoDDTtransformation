from FaultTree import *


def FTParse(filename):
    fts = {}
    with open(filename, "r") as file:
        for line in file:
            line = line.strip().replace('"', '').replace(';', '')
            linelist = line.split()
            if len(linelist) == 0:
                continue
            if "toplevel" in linelist[0]:
                top = linelist[1]
                continue
            name = linelist[0]
            if "or" in linelist[1]:
                FTtype = FtElementType.OR
                children = linelist[2:]

                ft_node = FT(name, FTtype, children)
                fts[name] = ft_node
            elif "and" in linelist[1]:
                FTtype = FtElementType.AND
                children = linelist[2:]

                ft_node = FT(name, FTtype, children)
                fts[name] = ft_node
            elif "prob" in linelist[1] or "lambda" in linelist[1]:
                prob = float(linelist[1].split('=')[1])
                if len(linelist) > 2 and 'cost' in linelist[2]:
                    cost = float(linelist[2].split('=')[1])
                else:
                    cost = None
                ft_node = FT(name, FtElementType.BE, prob=prob, cost=cost)
                fts[name] = ft_node
    for node in fts.values():
        if hasattr(node, "children") and node.children is not None:
            node.children = [fts[c] for c in node.children if c in fts]
    return fts[top]

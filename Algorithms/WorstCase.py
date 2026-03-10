from FaultTree.FaultTree import *
from FaultTree.FTParser import *

def WorstCost(ft):
    if ft.type == FtElementType.BE:
        return 1
    if ft.type == FtElementType.AND:
        if ft.children[0].prob <= ft.children[1].prob:
            # print("1: " + ft.children[0].name + " / " + ft.children[1].name)
            return WorstCost(ft.children[0])/ft.children[1].prob
        else:
            # print("2: " + ft.children[1].name + " / " + ft.children[0].name)
            return WorstCost(ft.children[1])/ft.children[0].prob

    if ft.type == FtElementType.OR:
        if ft.children[0].prob <= ft.children[1].prob:
            # print("3: " + ft.children[0].name + " / 1- " + ft.children[1].name)
            return WorstCost(ft.children[1])/(1-ft.children[0].prob)
        else:
            # print("4: " + ft.children[1].name + " / 1- " + ft.children[0].name)
            return WorstCost(ft.children[0])/(1-ft.children[1].prob)


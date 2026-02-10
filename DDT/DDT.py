from enum import Enum


class DdtElementType(Enum):
    DEC = 1
    ONE = 2
    ZERO = 3


class DDT:
    def __init__(self, name, ddtelement, children=None, prob=None, cost=None):
        if children is None:
            children = []
        self.name = name
        self.type = ddtelement
        self.children = children
        self.prob = prob
        self.cost = cost

    def fail_prob(self, ddt=None):
        if ddt is None:
            ddt = self
        if ddt.type == DdtElementType.ZERO:
            return 0
        if ddt.type == DdtElementType.ONE:
            return 1
        left = (1 - ddt.prob) * self.fail_prob(ddt.children[0])
        right = ddt.prob * self.fail_prob(ddt.children[1])
        return left + right

    def expected_height(self, ddt=None, depth=0):
        if ddt is None:
            ddt = self
        if ddt.type is not DdtElementType.DEC:
            return depth
        left = (1 - ddt.prob) * self.expected_height(ddt.children[0], depth + 1)
        right = ddt.prob * self.expected_height(ddt.children[1], depth + 1)
        return left + right

    def expected_cost(self, ddt=None):
        if ddt is None:
            ddt = self
        if ddt.type != DdtElementType.DEC:
            return 0  # leaf cost
        left = (1 - ddt.prob) * self.expected_cost(ddt.children[0])
        right = ddt.prob * self.expected_cost(ddt.children[1])
        return ddt.cost + left + right

    def find_vertex_by_name(self, name, ddt=None):
        if ddt is None:
            ddt = self
        if ddt.name == name:
            return ddt
        for child in ddt.children:
            result = self.find_vertex_by_name(name, child)
            if result is not None:
                return result
        return None

    def expected_cost_failure(self):
        expcost = 0
        failure_paths = [sublist for sublist in self.all_paths() if not sublist[-1].endswith('ZERO')]
        for path in failure_paths:
            cost = 0
            prob = 1
            for elem in path[:-1]:
                node = self.find_vertex_by_name(elem[0])
                cost += node.cost
                if elem[1] == 0:
                    prob *= (1 - node.prob)
                elif elem[1] == 1:
                    prob *= node.prob
            expcost += prob * cost
        return expcost

    def all_paths(self, path=None):
        if path is None:
            path = []

        if self.type == DdtElementType.DEC:
            paths = []
            left_paths = self.children[0].all_paths(path + [(self.name, 0)])
            right_paths = self.children[1].all_paths(path + [(self.name, 1)])
            paths.extend(left_paths)
            paths.extend(right_paths)
            return paths
        else:
            # Leaf node: return path + result
            return [path + [f"{self.type.name}"]]

    def check_duplicates(self, ddt=None):
        if ddt is None:
            ddt = self
        all = ddt.all_paths()
        duplicates = False
        while duplicates == False:
            for path in all:
                if len(path) != len(set(path)):
                    duplicates = True
            break
        return duplicates

    def remove_duplicate_vertices(self, ddt=None, seen=None):
        if seen is None:
            seen = set()
        if ddt is None:
            ddt = self
        for tup in seen:
            if tup[0] == ddt.name:
                if tup[1] == 0:
                    return ddt.children[0].remove_duplicate_vertices(seen=seen)
                if tup[1] == 1:
                    return ddt.children[1].remove_duplicate_vertices(seen=seen)
        if ddt.type != DdtElementType.DEC:
            return ddt
        child1 = self.remove_duplicate_vertices(ddt.children[0], seen=seen.union({(ddt.name, 0)}))
        child2 = self.remove_duplicate_vertices(ddt.children[1], seen=seen.union({(ddt.name, 1)}))
        return DDT(ddt.name, DdtElementType.DEC, children=[child1, child2], cost=ddt.cost, prob=ddt.prob)

    def print(self):
        print(self.to_string())

    def to_string(self, level=0):
        indent = "  " * level
        if self.cost is not None:
            result = f"{indent}- {self.name} (type: {self.type}, prob: {self.prob}, cost: {self.cost})\n"
        elif self.prob is not None:
            result = f"{indent}- {self.name} (type: {self.type}, prob: {self.prob})\n"
        else:
            result = f"{indent}- {self.name} (type: {self.type})\n"
        for child in self.children:
            result += child.to_string(level + 1)
        return result


def ddt_from_tuple(ddt, prob=None, cost=None):
    if isinstance(ddt, tuple):
        if cost is not None:
            p = prob[ddt[0]]
            c = cost[ddt[0]]
            return DDT(ddt[0], DdtElementType.DEC,
                       children=[ddt_from_tuple(ddt[1], prob, cost), ddt_from_tuple(ddt[2], prob, cost)], prob=p,
                       cost=c)
        elif prob is not None:
            p = prob[ddt[0]]
            return DDT(ddt[0], DdtElementType.DEC,
                       children=[ddt_from_tuple(ddt[1], prob), ddt_from_tuple(ddt[2], prob)], prob=p)
        return DDT(ddt[0], DdtElementType.DEC, children=[ddt_from_tuple(ddt[1], prob), ddt_from_tuple(ddt[2], prob)])
    elif ddt == '0':
        return DDT('ZERO', DdtElementType.ZERO)
    elif ddt == '1':
        return DDT('ONE', DdtElementType.ONE)



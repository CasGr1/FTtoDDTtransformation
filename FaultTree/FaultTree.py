from enum import Enum
from itertools import product
class FtElementType(Enum):
    BE = 1
    AND = 2
    OR = 3

class FT:
    def __init__(self, name, ftelement, children=None, prob=None, cost=None):
        if children == None:
            children = []
        self.name = name
        self.type = ftelement
        self.children = children
        self.prob = prob
        self.cost = cost

    def variables(self, ft=None):
        if ft is None:
            ft = self

        if ft.type == FtElementType.BE:
            return {ft.name}

        variables = set()
        for child in ft.children:
            variables.update(self.variables(child))
        return variables

    def vertices(self, ft=None):
        if ft is None:
            ft = self

        if ft.type == FtElementType.BE:
            return {ft.name}

        variables = {ft.name}
        for child in ft.children:
            variables.update(self.vertices(child))
        return variables

    def probabilities(self, ft=None):
        if ft is None:
            ft = self

        if ft.type == FtElementType.BE:
            return {ft.name: ft.prob}

        events = {}
        for child in ft.children:
            events.update(self.probabilities(child))
        return events

    def cost_dict(self, ft=None):
        if ft is None:
            ft = self

        if ft.type == FtElementType.BE:
            return {ft.name: ft.cost}

        events = {}
        for child in ft.children:
            events.update(self.cost_dict(child))
        return events

    def cut_set(self):
        cs = self._cut_set(self)
        return self.reduce_cut_sets(cs)

    def _cut_set(self, ft=None):
        if ft is None:
            ft = self

        if ft.type == FtElementType.BE:
            return [[ft.name]]

        if ft.type == FtElementType.AND:
            child_cut_sets = [self._cut_set(child) for child in ft.children]
            result = []

            for combination in product(*child_cut_sets):
                merged = []
                for cut in combination:
                    merged.extend(cut)
                result.append(sorted(set(merged)))
            return result

        if ft.type == FtElementType.OR:
            result = []
            for child in ft.children:
                new = self._cut_set(child)
                result += new
            return result

    def reduce_cut_sets(self, cut_sets):
        unique_sets = set(frozenset(lst) for lst in cut_sets)

        sorted_sets = sorted(unique_sets, key=len)

        result = []
        for s in sorted_sets:
            if not any(s.issuperset(r) for r in result):
                result.append(s)

        return [list(s) for s in result]

    def path_set(self):
        ps = self._path_set(self)
        return self.reduce_cut_sets(ps)

    def _path_set(self, ft=None):
        if ft is None:
            ft = self

        if ft.type == FtElementType.BE:
            return [[ft.name]]

        if ft.type == FtElementType.OR:
            child_cut_sets = [self._path_set(child) for child in ft.children]
            result = []

            for combination in product(*child_cut_sets):
                merged = []
                for cut in combination:
                    merged.extend(cut)
                result.append(sorted(set(merged)))
            return result

        if ft.type == FtElementType.AND:
            result = []
            for child in ft.children:
                new = self._path_set(child)
                result += new
            return result

    def unreliability(self, ft=None, add_unreliability=False):
        if ft is None:
            ft = self
        if ft.type == FtElementType.BE:
            return ft.prob

        if ft.type == FtElementType.AND:
            result = 1
            for child in ft.children:
                result *= self.unreliability(child, add_unreliability)
            if add_unreliability:
                ft.prob = result
            return result

        if ft.type == FtElementType.OR:
            result = 1
            for child in ft.children:
                result *= (1 - self.unreliability(child, add_unreliability))
            if add_unreliability:
                ft.prob = 1-result
            return 1 - result

    def find_vertex_by_name(self, name, ft=None):
        if ft is None:
            ft = self
        if ft.name == name:
            return ft
        for child in ft.children:
            result = self.find_vertex_by_name(name, child)
            if result is not None:
                return result
        return None


    def shape(self):
        visited = {}

        def dfs(node):
            node_id = id(node)

            if node_id in visited:
                return node.name

            visited[node_id] = node.name

            for child in node.children:
                result = dfs(child)
                if result is not None:
                    return result
            return None

        duplicate = dfs(self)
        return "TREE" if duplicate is None else duplicate

    def max_height(self, ft=None, height = 1):
        if ft is None:
            ft = self
        if ft.type == FtElementType.BE:
            return height

        total_height = height
        for child in ft.children:
            temp_height = self.max_height(child, height+1)
            if temp_height > total_height:
                total_height = temp_height
        return total_height

    def print(self, indent=0, visited=None):
        if visited is None:
            visited = set()

        prefix = " " * indent

        # cycle / shared-node detection
        if self.name in visited:
            print(prefix + f"{self.name} (↺ already printed)")
            return

        visited.add(self.name)

        if self.cost is not None:
            print(prefix + f"{self.name} prob: {self.prob} cost: {self.cost} (", end="")
        elif self.prob is not None:
            print(prefix + f"{self.name} prob: {self.prob} (", end="")
        else:
            print(prefix + f"{self.name} (", end="")

        if self.type == FtElementType.BE:
            print("BE)")
        elif self.type == FtElementType.AND:
            print("AND)")
        elif self.type == FtElementType.OR:
            print("OR)")

        for child in getattr(self, "children", []):
            child.print(indent + 1, visited)




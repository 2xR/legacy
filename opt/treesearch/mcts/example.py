from itertools import izip
from collections import namedtuple
from utils import attr
from opt.treesearch.mcts import MCTS


Item = namedtuple("Item", ["name", "value", "weight", "ratio"])


def new_item(name, value, weight):
    return Item(name, value, weight, float(value) / weight)


def solve_and_verify(instance):
    items, k, opt_sol = instance
    mcts = KnapsackMCTS()
    mcts.init(instance=(items, k), cpu_limit=60)
    mcts.params.report()
    mcts.run()
    packed_items = set(mcts.solutions.best().data)
    if mcts.termination is mcts.TERMINATION.OPTIMAL:
        assert packed_items == opt_sol
    return mcts


def instance1():
    k = 165
    w = [23, 31, 29, 44, 53, 38, 63, 85, 89, 82]
    v = [92, 57, 49, 68, 60, 43, 67, 84, 87, 72]
    s = [1, 1, 1, 1, 0, 1, 0, 0, 0, 0]
    items = [new_item(*data) for data in izip(xrange(len(w)), v, w)]
    sol = {items[i] for i in xrange(len(s)) if s[i] == 1}
    return items, k, sol


def instance2():
    k = 26
    w = [12, 7, 11, 8, 9]
    v = [24, 13, 23, 15, 16]
    s = [0, 1, 1, 1, 0]
    items = [new_item(*data) for data in izip(xrange(len(w)), v, w)]
    sol = {items[i] for i in xrange(len(s)) if s[i] == 1}
    return items, k, sol


def instance8():
    k = 6404180
    w = [382745, 799601, 909247, 729069, 467902, 44328, 34610, 698150,
         823460, 903959, 853665, 551830, 610856, 670702, 488960, 951111,
         323046, 446298, 931161, 31385, 496951, 264724, 224916, 169684]
    v = [825594, 1677009, 1676628, 1523970, 943972, 97426, 69666, 1296457,
         1679693, 1902996, 1844992, 1049289, 1252836, 1319836, 953277, 2067538,
         675367, 853655, 1826027, 65731, 901489, 577243, 466257, 369261]
    s = [1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1]
    items = [new_item(*data) for data in izip(xrange(len(w)), v, w)]
    sol = {items[i] for i in xrange(len(s)) if s[i] == 1}
    return items, k, sol


class KnapsackMCTS(MCTS):
    class ParamSet(MCTS.ParamSet):
        class Defaults(MCTS.ParamSet.Defaults):
            pruning = True
            expansion_limit = 2

    class Node(MCTS.Node):
        __slots__ = ("items_remaining",
                     "items_packed",
                     "capacity_required",
                     "capacity_remaining",
                     "total_value")

        @classmethod
        def root(cls, solver):
            items, capacity = solver.instance[:2]
            root = cls()
            root.items_remaining = sorted(items, key=attr.getter("ratio"), reverse=True)
            root.items_packed = []
            root.capacity_required = sum(item.weight for item in items)
            root.capacity_remaining = capacity
            root.total_value = 0.0
            return root

        def copy(self):
            clone = type(self)()
            clone.items_remaining = list(self.items_remaining)
            clone.items_packed = list(self.items_packed)
            clone.capacity_required = self.capacity_required
            clone.capacity_remaining = self.capacity_remaining
            clone.total_value = self.total_value
            return clone

        sense = max

        def objective(self):
            return self.total_value

        def bound(self):
            bound = self.total_value
            capacity = self.capacity_remaining
            for item in self.items_remaining:
                if item.weight <= capacity:
                    bound += item.value
                    capacity -= item.weight
                else:
                    bound += float(item.value * capacity) / item.weight
                    break
            return bound

        def is_leaf(self):
            return len(self.items_remaining) == 0

        def branches(self):
            return True, False

        def apply(self, pack):
            item = self.items_remaining.pop(0)
            self.capacity_required -= item.weight
            if pack:
                self.items_packed.append(item)
                self.total_value += item.value
                self.capacity_remaining -= item.weight
                self.items_remaining = [i for i in self.items_remaining
                                        if i.weight <= self.capacity_remaining]
                self.capacity_required = sum(i.weight for i in self.items_remaining)

            elif self.capacity_required <= self.capacity_remaining:
                self.total_value += sum(i.value for i in self.items_remaining)
                self.capacity_remaining -= sum(i.weight for i in self.items_remaining)
                self.capacity_required = 0.0
                self.items_packed.extend(self.items_remaining)
                self.items_remaining = []

        def solution_and_meta(self):
            return self.items_packed, {}

        def simulation(self):
            node = self.copy()
            while len(node.items_remaining) > 0:
                node.apply(True)
            return node

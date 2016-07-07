from math import floor, ceil
from utils.math import mean
from utils.prettyrepr import prettify_class

from .rule import BranchingRule


@prettify_class
class PseudocostData(object):
    __slots__ = ("registry",
                 "var_name",
                 "total",
                 "count")

    def __init__(self, registry, var_name):
        self.registry = registry
        self.var_name = var_name
        self.total = 0.0
        self.count = 0.0

    def __info__(self):
        avg = self.mean if self.initialized else "???"
        return "{}={}, <total={}, count={}>".format(self.var_name, avg, self.total, self.count)

    @property
    def initialized(self):
        return self.count > 0.0

    @property
    def mean(self):
        count = self.count
        if count > 0.0:
            return self.total / count
        else:
            return self.registry.mean

    def record(self, pscost):
        self.total += pscost
        self.count += 1.0
        if self.count == 1.0:
            self.registry.initialized.add(self)


class PseudocostRegistry(dict):
    __slots__ = ("initialized",)

    def __init__(self, vars):
        dict.__init__(self, {v: PseudocostData(self, v) for v in vars})
        self.initialized = set()

    @property
    def mean(self):
        if len(self.initialized) == 0:
            return 1.0
        else:
            return mean(pscost.mean for pscost in self.initialized)


class PseudocostBranching(BranchingRule):
    def __init__(self, model=None):
        self.down_pscost = None
        self.up_pscost = None
        BranchingRule.__init__(self, model)

    def init(self, model):
        BranchingRule.init(self, model)
        self.down_pscost = PseudocostRegistry(self.relaxation.vars)
        self.up_pscost = PseudocostRegistry(self.relaxation.vars)

    def branching_score(self, var_name, node):
        var_value = node.relax_sol[var_name]
        down_delta = var_value - floor(var_value)
        up_delta = ceil(var_value) - var_value
        return self.merged_score(down_delta * self.down_pscost[var_name].mean,
                                 up_delta * self.up_pscost[var_name].mean)

    def record_branching(self, var_name, parent, children):
        down, up = children
        if down.is_feasible:
            self._record_pseudocost(self.down_pscost, var_name, parent, down)
        if up.is_feasible:
            self._record_pseudocost(self.up_pscost, var_name, parent, up)

    @staticmethod
    def _record_pseudocost(pscost_registry, var_name, parent, child):
        delta_obj = child.relax_obj - parent.relax_obj
        delta_var = abs(child.relax_sol[var_name] - parent.relax_sol[var_name])
        if delta_var != 0.0:
            pscost_registry[var_name].record(delta_obj / delta_var)

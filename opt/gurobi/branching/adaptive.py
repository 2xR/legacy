"""
WIP:
 the idea of this branching rule is to have a registry of pseudocost data created for each part
 of the tree where actual branching costs differ significantly from that node's reference
 pseudocost registry.
"""

from math import floor, ceil
from utils.misc import INF

from .rule import BranchingRule
from .reliability import ReliabilityBranching


class AdaptivePseudocostData(dict):
    __slots__ = ()

    def __getitem__(self, node):
        while node not in self:
            node = node.parent
        return dict.__getitem__(self, node)

    def add(self, node):
        self[node] = PseudocostData(self.registry, )

    def record(self):
        pass


class AdaptiveBranching(BranchingRule):
    def __init__(self, model=None):
        BranchingRule.__init__(self, model)
        self.down_pscost = None
        self.up_pscost = None

    def init(self, model):
        BranchingRule.init(self, model)
        self.down_pscost = {v: AdaptivePseudocostData() for v in self.relaxation.vars}
        self.up_pscost = {v: AdaptivePseudocostData() for v in self.relaxation.vars}

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
        delta_var = abs(child.relax_sol[var_name] - parent.relax_sol[var_name])
        delta_obj = child.relax_obj - parent.relax_obj
        if delta_var != 0.0:
            pscost_registry[var_name].record(delta_obj / delta_var)


# class TreePseudocostRegistry(PseudocostRegistry):
#     __slots__ = ("parent",)
#
#
#
# class PseudocostBranching(BranchingRule):
#     def __init__(self, model=None):
#         BranchingRule.__init__(self, model)
#         self.down_pscost = None
#         self.up_pscost = None
#         self.pscost = {}
#
#     def init(self, model):
#         BranchingRule.init(self, model)
#         self.down_pscost = PseudocostRegistry(self.relaxation.vars)
#         self.up_pscost = PseudocostRegistry(self.relaxation.vars)
#
#     def root(self):
#         root = BranchingRule.root(self)
#         self.pscost = {root: (self.down_pscost, self.up_pscost)}
#
#     def branching_score(self, var_name, node):
#         var_value = node.relax_sol[var_name]
#         down_delta = var_value - floor(var_value)
#         up_delta = ceil(var_value) - var_value
#         return self.merged_score(down_delta * self.down_pscost[var_name].mean,
#                                  up_delta * self.up_pscost[var_name].mean)
#
#     def record_branching(self, var_name, parent, children):
#         for child, pscost_registry in izip(children, self.pscost):
#             if child.relax_sol is not None:
#                 delta_var = abs(child.relax_sol[var_name] - parent.relax_sol[var_name])
#                 delta_obj = child.relax_obj - parent.relax_obj
#                 if delta_var != 0.0:
#                     pscost_registry[var_name].record(delta_obj / delta_var)
#
#
# class AdaptiveBranching(ReliabilityBranching):
#     __info_attrs__ = ReliabilityBranching.__info_attrs__ + ("max_spread",)
#
#     def __init__(self, cand_lookahead=INF, min_reliability=1,
#                  max_rel_spread=1.0, max_abs_spread=0.0, model=None):
#         self.max_rel_spread = max_rel_spread
#         self.max_abs_spread = max_abs_spread
#         ReliabilityBranching.__init__(self, cand_lookahead, min_reliability, model)
#
#     def

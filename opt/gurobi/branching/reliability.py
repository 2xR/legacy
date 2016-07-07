from utils.misc import INF

from .strong import StrongBranching
from .pseudocost import PseudocostBranching


class ReliabilityBranching(StrongBranching):
    __info_attrs__ = StrongBranching.__info_attrs__ + ("min_reliability",)

    def __init__(self, cand_lookahead=INF, min_reliability=1, model=None):
        self.min_reliability = min_reliability
        StrongBranching.__init__(self, cand_lookahead, model)

    def reliability(self, var_name):
        return min(self.down_pscost[var_name].count, self.up_pscost[var_name].count)

    def branching_score(self, var_name, node):
        if self.reliability(var_name) >= self.min_reliability:
            return PseudocostBranching.branching_score(self, var_name, node)
        else:
            return StrongBranching.branching_score(self, var_name, node)

    record_branching = PseudocostBranching.record_branching

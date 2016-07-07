from functools import partial

from utils.misc import INF
from utils.collectors import Average
from opt.gurobi.misc import temporary_params

from .pseudocost import PseudocostBranching


class StrongBranching(PseudocostBranching):
    __info_attrs__ = ("cand_lookahead",)

    def __init__(self, cand_lookahead=INF, model=None):
        self.cand_lookahead = cand_lookahead
        self.mean_simplex_iters = Average()
        PseudocostBranching.__init__(self, model)

    def reset(self):
        self.mean_simplex_iters.reset()
        PseudocostBranching.reset(self)

    def select_variable(self, node, rng):
        pscost_score = partial(PseudocostBranching.branching_score, self, node=node)
        sorted_vars = sorted(node.fractional_vars, key=pscost_score, reverse=True)
        best_vars = []
        best_score = -INF
        stagnation = 0
        for var_name in sorted_vars:
            var_score = self.branching_score(var_name, node)
            if var_score > best_score:
                best_vars = [var_name]
                best_score = var_score
                stagnation = 0
            elif var_score == best_score:
                best_vars.append(var_name)
            else:
                stagnation += 1
                if stagnation >= self.cand_lookahead:
                    break
        return rng.choice(best_vars)

    def branching_score(self, var_name, node):
        try:
            max_iters = 2.0 * max(1.0, self.mean_simplex_iters.value)
        except ZeroDivisionError:
            max_iters = INF
        with temporary_params(self.relaxation.model, IterationLimit=max_iters):
            children = []
            for partial_sol in node.branch_partial_sols(var_name):
                child = type(node)(self, partial_sol)
                children.append(child)
                self.mean_simplex_iters.collect(self.relaxation.model.IterCount)
            PseudocostBranching.record_branching(self, var_name, node, children)
            delta_objs = [child.relax_obj - node.relax_obj
                          for child in children
                          if child.relax_sol is not None]
        if len(delta_objs) == 2:
            return self.merged_score(*delta_objs)
        elif len(delta_objs) == 1:
            return abs(delta_objs[0])
        elif len(delta_objs) == 0:
            return INF
        else:
            raise Exception("unexpected number of children")

    def record_branching(self, var_name, parent, children):
        """Since pseudocosts are being recorded during strong branching variable evaluations
        (inside branching_score()), we do not need to (and should not) record the same branching
        costs when actually taking the branching decision."""
        pass

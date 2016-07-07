from opt.gurobi import integrality

from .rule import BranchingRule


class LeastInfeasibleBranching(BranchingRule):
    def branching_score(self, var_name, node):
        return integrality(node.relax_sol[var_name])

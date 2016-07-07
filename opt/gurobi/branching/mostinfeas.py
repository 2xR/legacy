from opt.gurobi import fractionality

from .rule import BranchingRule


class MostInfeasibleBranching(BranchingRule):
    def branching_score(self, var_name, node):
        return fractionality(node.relax_sol[var_name])

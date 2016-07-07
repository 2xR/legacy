from .rule import BranchingRule


class RandomBranching(BranchingRule):
    def branching_score(self, var_name, node):
        return 0.0

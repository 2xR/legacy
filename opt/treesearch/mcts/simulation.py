from collections import Sequence
from opt.treesearch import TreeNode


def random_simulation(metanode):
    """Given a metanode, apply (uniform) randomly selected actions/branches to the node until a
    leaf is reached.  This method operates on a copy of the metanode's node, so it can be used
    directly as a simulation policy.  In fact, this is the default simulation policy used in MCTS.
    """
    random_choice = metanode.solver.rng.choice
    node = metanode.node.copy()
    while not node.is_leaf():
        branches = node.branches()
        if not isinstance(branches, Sequence):
            branches = list(branches)
        if len(branches) == 0:
            break
        branch = random_choice(branches)
        if isinstance(branch, TreeNode):
            node = branch
        else:
            node.apply(branch)
    return node

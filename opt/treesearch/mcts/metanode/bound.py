from utils.approx import Approx


class MetaNodeBound(object):
    """
    Manages the objective function bound in a metanode.  When the metanode is fully expanded, its
    bound can be updated (i.e. tightened) to the best bound of its children, and propagated upwards
    to the root.  If the root metanode's bound is updated, the solver's bound is also automatically
    updated to the new best bound in the tree.
    """
    __slots__ = ("metanode", "value")

    def __init__(self, metanode):
        self.metanode = metanode
        self.value = metanode.node.bound()
        assert self.value is not None

    def best_from_children(self):
        metanode = self.metanode
        best_in = metanode.solver.sense.best_in
        return best_in(child.bound.value for child in metanode.children)

    def update_from_children(self):
        metanode = self.metanode
        if metanode.is_expandable:
            raise Exception("cannot update bound: one or more branches remain unexpanded")
        solver = self.metanode.solver
        is_better = solver.sense.is_better
        while metanode is not None:
            bound = metanode.bound
            old = bound.value
            new = bound.best_from_children()
            if old == new:
                break
            assert is_better(old, new) or Approx(old) == new
            bound.value = new
            metanode = metanode.parent
        else:
            if is_better(solver.bound, solver.root.bound.value):
                solver.bound = solver.root.bound.value

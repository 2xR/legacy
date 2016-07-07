from collections import Sequence
from sys import stdout

from utils.misc import INF
from utils.graph import tree
from utils import attr

from opt import Infeasible
from opt.treesearch import TreeNode

from .bound import MetaNodeBound
from .stats import MetaNodeStats
from .branches import MetaNodeBranches


class MetaNode(object):
    """
    A MetaNode object attaches itself to a TreeNode object, encapsulating information that
    is relevant for Monte Carlo tree search.
    """
    __slots__ = ("solver",    # reference to an MCTS solver object
                 "node",      # the TreeNode being wrapped by this meta node
                 "parent",    # parent meta-node
                 "children",  # list of active child meta-nodes
                 "branches",  # branches awaiting expansion
                 "bound",     # best objective value bound in this subtree
                 "stats")     # simulation statistics

    def __init__(self, solver, node):
        self.solver = solver
        self.node = node
        self.parent = None
        self.children = []
        self.branches = MetaNodeBranches(self)
        self.bound = None
        self.stats = None
        if not node.is_leaf():
            if solver.params.pruning:
                self.bound = MetaNodeBound(self)
            if not self.is_prunable:
                self.branches.init()
                if self.is_expandable:
                    self.stats = MetaNodeStats(self)

    def __len__(self):
        """Number of children of this node."""
        return len(self.children)

    def __iter__(self):
        """Iterating over a metanode corresponds to iterating over its children."""
        return iter(self.children)

    def __getitem__(self, i):
        """meta[i] is short for meta.children[i], and meta[i,j,(...)] is short for
        meta.children[i].children[j].children[(...)]"""
        if isinstance(i, int):
            return self.children[i]
        elif isinstance(i, Sequence):
            meta = self
            for j in i:
                meta = meta.children[j]
            return meta
        else:
            raise TypeError("expecting integer or sequence of integers")

    # ------------------------------------------------------------------------------
    @property
    def size(self):
        """Return the size (# of nodes) of the tree rooted at 'self'."""
        count = 0
        stack = [self]
        while len(stack) > 0:
            meta = stack.pop()
            count += 1
            if len(meta.children) > 0:
                stack.extend(meta.children)
        return count

    @property
    def height(self):
        """Return the height (# of levels) of the tree rooted at 'self'."""
        height = 1
        stack = [(self, 1)]
        while len(stack) > 0:
            meta, level = stack.pop()
            height = max(height, level)
            if len(meta.children) > 0:
                level += 1
                stack.extend((child, level) for child in meta.children)
        return height

    @property
    def dimensions(self):
        """Return the size (# of nodes) and height (# of levels) of the tree rooted at 'self'."""
        return self.size, self.height

    @property
    def rpath(self):
        """The reverse path of a metanode 'm' is the sequence of metanodes starting at 'm' and
        ending at the root metanode."""
        metanode = self
        while metanode is not None:
            yield metanode
            metanode = metanode.parent

    @property
    def path(self):
        """The sequence of nodes from the root of the tree to 'self'."""
        path = list(self.rpath)
        path.reverse()
        return path

    @property
    def depth(self):
        """Number of nodes above this node, i.e. the number of nodes in the path between this node
        (exclusive) and the root (inclusive)."""
        depth = 0
        parent = self.parent
        while parent is not None:
            depth += 1
            parent = parent.parent
        return depth

    @property
    def mean_depth(self):
        """Mean depth of *all* nodes of this tree."""
        total_depth = 0
        total_nodes = 0
        stack = [(self, 0)]
        while len(stack) > 0:
            metanode, depth = stack.pop()
            total_depth += depth
            total_nodes += 1
            if len(metanode.children) > 0:
                depth += 1
                stack.extend((child, depth) for child in metanode.children)
        return float(total_depth) / total_nodes

    @property
    def mean_leaf_depth(self):
        """Mean depth of the *leaf* nodes of this tree. Note that leaf here does not necessarily
        refer to a node containing an actual complete solution (or an infeasible subproblem), but
        a node which has no children at the time of the call."""
        total_depth = 0
        total_leaves = 0
        stack = [(self, 0)]
        while len(stack) > 0:
            metanode, depth = stack.pop()
            if len(metanode.children) > 0:
                depth += 1
                stack.extend((child, depth) for child in metanode.children)
            else:
                total_depth += depth
                total_leaves += 1
        return float(total_depth) / total_leaves

    @property
    def is_prunable(self):
        """A metanode is prunable if its bound is not better than the incumbent."""
        bound = self.bound
        solver = self.solver
        return bound is not None and not solver.sense.is_better(bound.value, solver.incumbent)

    @property
    def is_expandable(self):
        """A node is expandable while it has unexpanded branches."""
        return self.branches.remaining is not None

    @property
    def is_bound_updatable(self):
        """True if the bound can be updated to the best bound of this node's children, i.e. when
        the node has been completely expanded and has at least one child node left."""
        return (self.bound is not None and
                len(self.children) > 0 and
                self.branches.remaining is None)

    @property
    def is_exhausted(self):
        """A node is exhausted if it is fully expanded and all its children have been
        exhausted and thus removed from the tree."""
        return self.branches.remaining is None and len(self.children) == 0

    # ------------------------------------------------------------------------------
    def create_next_child(self):
        """Creates a new metanode for the next unexpanded branch of this node.  Returns None if
        the child metanode is prunable or a leaf, otherwise returns the newly created metanode.
        Note that, after this call, the child metanode must still be added to the tree with
        add_child() and the branches of the parent metanode must be advance()d, otherwise
        subsequent calls to this method will produce the same child node."""
        # create the child node from the next unexpanded branch
        branch = self.branches.next
        if isinstance(branch, TreeNode):
            child_node = branch
        else:
            child_node = self.node.copy()
            child_node.apply(branch)
        # create child metanode and check if it is prunable or non-expandable (i.e. leaf)
        solver = self.solver
        child_metanode = type(self)(solver, child_node)
        if child_metanode.is_prunable:
            solver.channel.emit(solver.SIGNALS.PRUNING_NODE, child_metanode)
            return None
        if not child_metanode.is_expandable:
            solver.solutions.check(child_node)
            self.stats.discard_sim_result(solver.objective(child_node))
            return None
        return child_metanode

    def add_child(self, child):
        """Add a child to this metanode."""
        assert child.stats.sim_count == 0
        self.children.append(child)
        child.parent = self

    def remove_child(self, child, update_bound=True):
        """Remove 'child' from 'self'.  If the parent metanode becomes exhausted (i.e. is fully
        expanded and becomes empty) afterwards, the removal is propagated up.  Metanode stats and
        bounds are updated accordingly."""
        if len(child.children) > 0:
            raise Exception("attempting to remove non-empty child")
        parent = self
        while True:
            # unlink child from parent
            parent.children.remove(child)
            child.parent = None
            # remove child sim result from parent stats
            assert child.stats.sim_count in (0, 1)
            if child.stats.sim_count == 1:
                parent.stats.remove_sim_result(child.stats.sim_result)
            # recompute parent bound (and propagate up) if necessary
            if (((update_bound and
                  parent.is_bound_updatable and
                  parent.bound.value == child.bound.value))):
                parent.bound.update_from_children()
            # if this node just became exhausted, we move one level up and continue removing
            if parent.is_exhausted and parent.parent is not None:
                child = parent
                parent = parent.parent
            else:
                break

    def on_expansion_complete(self):
        """This method is called automatically by the branches object when it finds that there are
        no more unexpanded branches in this node.  This removes the node from the tree if it is
        exhausted, otherwise updates its bound to the best bound of its children (if pruning is
        enabled of course).
        At this point, if the metanode remains in the tree, node data can be released by the
        release_node() method.  By default, this method calls the node's own release() method,
        which must return an object that will replace the node reference in the metanode.
        To fully release the node from memory, simply return None (the default implementation) in
        the node's release() method or set node to None in the metanode's release_node() method.
        To keep the node data return self in the node's release() method, or do nothing in the
        metanode's release_node() method.
        Since node data is usually no longer used after expansion, releasing it is *very* helpful
        in long-running solvers."""
        if self.parent is not None and self.is_exhausted:
            self.parent.remove_child(self)
        else:
            if self.is_bound_updatable:
                self.bound.update_from_children()
            self.release_node()

    def release_node(self):
        self.node = self.node.release()

    # ------------------------------------------------------------------------------
    def chop(self):
        """Remove a node and the whole subtree under it from the tree."""
        stack = [self]
        while len(stack) > 0:
            metanode = stack.pop()
            if len(metanode.children) == 0 and metanode.parent is not None:
                metanode.parent.remove_child(metanode, update_bound=False)
            else:
                if metanode.is_expandable:
                    # if the metanode is still expandable, we must explicitly remove
                    # it because removing all its children will not propagate up (the
                    # node is not exhausted even if it becomes empty, because not all
                    # its children have been expanded yet)
                    stack.append(metanode)
                stack.extend(metanode.children)
        # only now do we update the parent's bound (if applicable)
        parent = self.parent
        if (((parent is not None and
              parent.is_bound_updatable and
              parent.bound.value == self.bound.value))):
            parent.bound.update_from_children()

    def prune(self, cutoff):
        """Prune the (sub-)tree under this node using the argument objective cutoff."""
        solver = self.solver
        is_better = solver.sense.is_better
        pruned_count = 0
        stack = [self]
        while len(stack) > 0:
            metanode = stack.pop()
            if not is_better(metanode.bound.value, cutoff):
                solver.channel.emit(solver.SIGNALS.PRUNING_NODE, metanode)
                pruned_count += metanode.size
                metanode.chop()
            elif len(metanode.children) > 0:
                stack.extend(metanode.children)
        self.solver.log.debug("tree pruning removed {} nodes".format(pruned_count))

    # ------------------------------------------------------------------------------
    def iter_depth_first(self, max_depth=INF):
        """Iterates over the metanodes in this tree using depth-first order.
        Yields (metanode, depth) tuples."""
        stack = [(self, 0)]
        while len(stack) > 0:
            metanode, depth = stack.pop()
            yield metanode, depth
            if depth < max_depth and len(metanode.children) > 0:
                depth += 1
                stack.extend((child, depth) for child in metanode.children)

    def report(self, max_depth=1, ostream=stdout):
        """Write a summary report of metanode statistics in a tree-like format using indentation
        to indicate parent-child relationships."""
        for metanode, depth in self.iter_depth_first(max_depth):
            metanode.stats.report(indent=depth, ostream=ostream)

    def validate(self, max_depth=INF):
        """Validate metanode statistics in the tree rooted at this node."""
        for metanode, depth in self.iter_depth_first(max_depth):
            metanode.stats.validate()

    # ------------------------------------------------------------------------------
    @staticmethod
    def default_edge_weight(parent, child):
        sim_best = child.stats.sim_best_result
        return None if isinstance(sim_best, Infeasible) else sim_best

    def to_networkx(self, edge_weight=None):
        """Creates a networkx digraph representing this tree.  Edge weights can be specified by
        the 'edge_weight' parameter which should be a function taking parent and child metanodes
        as arguments (by default this uses MetaNodeStats.default_edge_weight())."""
        if edge_weight is None:
            edge_weight = self.default_edge_weight
        return tree.build(root=self,
                          get_children=attr.getter("children"),
                          get_edge_weight=edge_weight)

    def draw(self, highlight_paths=(), axes=None, show=True):
        """Creates a simple figure with the current state of the tree."""
        return tree.draw(self.to_networkx(),
                         root=self,
                         highlight_paths=highlight_paths,
                         axes=axes,
                         show=show)

from opt.solver.solver import Solver

from .node import TreeNode
from .opt.treesearch.queuebased.queue import NodeQueue, CheckQueue
from .opt.treesearch.queuebased.params import TreeSearchParamSet


class TreeSearch(Solver):
    """
    A generic queue-based tree search solver.  This class can be used as a base to create several
    variants of tree search that used a queue for open nodes, including DFS, BFS, Best-First, and
    Multi-Queue Tree Search.  These algorithms share the same overall structure, varying only the
    policies that control how nodes are added and removed from the queue.
    """
    ParamSet = TreeSearchParamSet  # parameter set class used by the solver
    Queue = NodeQueue              # queue class used by the solver
    Node = TreeNode                # tree node class used by the solver
    default_plugins = list(Solver.default_plugins) + [CheckQueue]

    @Solver.uninitialized.on_enter
    def uninitialized(self):
        Solver.uninitialized.enter(self)
        self.queue = self.Queue()  # data structure used for keeping open nodes

    def _bootstrap(self):
        """Bootstrapping in tree search consists of generating the root node and putting in the
        queue.  The bound may also be updated if we're using pruning."""
        root = self.params.root_fnc(self)
        self.queue.put(root)
        if self.params.pruning:
            root_bound = root.bound()
            if self.objective.sense.is_better(self.bound, root_bound):
                self.bound = root_bound

    def _iterate(self):
        """An iteration of the tree search. First, an element is taken from the queue. A queue
        element may be either a TreeNode or a (parent, branch) pair which allows us to create a new
        node.
        If the element taken from the queue is a TreeNode object, the node's branches are expanded
        into the queue (because the node would not even be in the queue if it were a leaf or its
        bound was not better than the incumbent).
        If the element taken from the queue is a (parent, branch) pair, we make a copy of the
        parent node and apply the branch to it. Then, we check if the modified node is a leaf, and
        finally apply pruning (if applicable) and expand its branches into the queue."""
        elem = self.queue.get()
        if isinstance(elem, TreeNode):
            self._expand_node(elem)
        else:
            parent, branch = elem
            child = parent.copy()
            child.apply(branch)
            if child.is_leaf():
                self.solutions.check(child)
            elif (not self.params.pruning or
                  self.objective.sense.is_better(child.bound(), self.incumbent)):
                self._expand_node(child)

    def _expand_node(self, node):
        """Expand the node's branch list into the queue."""
        branches = 0
        is_better = self.objective.sense.is_better
        for branch in node.branches():
            if isinstance(branch, TreeNode):
                if branch.is_leaf():
                    self.solutions.check(branch)
                elif not self.params.pruning or is_better(branch.bound(), self.incumbent):
                    self.queue.put(branch)
            else:
                self.queue.put((node, branch))
            branches += 1
        if branches == 0:
            self.solutions.check(node)

    def _extract_solution_and_meta(self, node):
        return node.solution_and_meta()

    # def report(self, show_solutions=True, ostream=stdout):
    #     """Print a summary of the solver's configuration, current search state and solutions found
    #     so far."""
    #     line_fmt = "%30s: %s\n"
    #     ostream.write(repr(self) + "\n")
    #     if self.instance is None:
    #         ostream.write("No instance available. Nothing to report.\n")
    #         return
    #     search_speed = (self.iterations.total / self.cpu.total) if self.cpu.total > 0.0 else NAN
    #     for key, value in [("Queue size",      len(self.queue)),
    #                        ("Search speed",    "%.3f iter/sec" % search_speed),
    #                        ("Total CPU time",  self.cpu.total),
    #                        ("Iterations",      self.iterations.total),
    #                        ("Improvements",    self.improvements.total),
    #                        ("Upper bound",     self.upper_bound),
    #                        ("Lower bound",     self.lower_bound),
    #                        ("Pruning enabled", self.pruning),
    #                        ("Solutions",       len(self.solutions))]:
    #         ostream.write(line_fmt % (key, value))
    #     if show_solutions:
    #         for x, sol in enumerate(self.solutions):
    #             obj = sol.meta.objective
    #             cpu = sol.meta.cpu
    #             ostream.write(line_fmt % (x, "z = %s (obtained at %s)" % (obj, cpu)))

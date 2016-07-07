from sys import stdout
from collections import deque
from utils.misc import INF

from opt.solver import Solver, Plugin

from .node import TreeNode


class NodeQueue(deque):
    """
    Base class for node queue classes.  This is where the tree search stores nodes for later
    exploration.  The policies defining how to put and get nodes from the queue basically
    determine the exploration order of the nodes.  See DFS_NodeQueue and BFS_NodeQueue for
    the simplest examples.
    """
    def put(self, elem):
        raise NotImplementedError()

    def get(self):
        raise NotImplementedError()

    def prune(self, cutoff, is_better):
        for _ in xrange(len(self)):
            elem = self[0]
            if isinstance(elem, TreeNode):
                node = elem
            else:
                node, branch = elem
            if is_better(node.bound(), cutoff):
                self.rotate(-1)
            else:
                self.popleft()

    def pprint(self, start=0, n=INF, ostream=stdout):
        """Starting from index 'start', print 'n' elements in the queue."""
        for x in xrange(start, min(start + n, len(self))):
            ostream.write("\t{} :: {}\n".format(x, self[x]))

    def pprint_start(self, n=10, ostream=stdout):
        """Print the first n elements in the queue."""
        n = min(n, len(self))
        ostream.write("Showing first {} elements in the queue\n".format(n))
        self.pprint(0, n, ostream)

    def pprint_end(self, n=10, ostream=stdout):
        """Print the last n elements in the queue."""
        n = min(n, len(self.queue))
        ostream.write("Showing last {} elements in the queue\n".format(n))
        self.pprint(len(self)-n, n, ostream)

    def pprint_edges(self, n=5, ostream=stdout):
        """Print the first and last n elements in the queue."""
        if len(self) <= 2 * n:
            ostream.write("Showing all elements\n")
            self.pprint(0, len(self), ostream)
        else:
            self.pprint_start(n, ostream)
            self.pprint_end(n, ostream)


class DFS_NodeQueue(NodeQueue):
    put = NodeQueue.append
    get = NodeQueue.pop


class BFS_NodeQueue(NodeQueue):
    put = NodeQueue.append
    get = NodeQueue.popleft


NodeQueue.DFS = DFS_NodeQueue
NodeQueue.BFS = BFS_NodeQueue


class CheckQueue(Plugin):
    """
    This solver plugin is automatically included in queue-based tree search solvers.  It check,
    at the end of each iteration, if the node queue is empty.  When the queue becomes empty, the
    solver is interrupted and the search finishes.
    """
    EMPTY_QUEUE = "node queue is empty"

    signal_map = {Solver.SIGNALS.ITERATION_FINISHED: "check"}
    emits = {EMPTY_QUEUE}

    def check(self, listener):
        if len(self.solver.queue) == 0:
            self.solver.channel.emit(self.EMPTY_QUEUE)
            self.solver.interrupts.add("node queue is empty", Solver.ACTION.FINISH)

"""
A simple test to validate the tree search algorithm and the depth-first and breadth-first queues.
"""
from opt.treesearch import TreeNode, NodeQueue, TreeSearch


class FooNode(TreeNode):
    @classmethod
    def root(cls, solver):
        root = cls()
        root.solver = solver
        root.selected = []
        root.remaining = range(solver.instance)
        solver.meta.leaves_visited = 0
        return root

    def copy(self):
        clone = type(self)()
        clone.solver = self.solver
        clone.selected = list(self.selected)
        clone.remaining = list(self.remaining)
        return clone

    def is_leaf(self):
        print "solution:", self.selected
        if len(self.selected) == self.solver.instance:
            self.solver.meta.leaves_visited += 1
            return True
        return False

    def branches(self):
        return reversed(self.remaining)

    def apply(self, value):
        self.selected.append(value)
        self.remaining.remove(value)

    def objective(self):
        return self.solver.rng.random()


class FooDFS(TreeSearch):
    Node = FooNode
    Queue = NodeQueue.DFS


class FooBFS(TreeSearch):
    Node = FooNode
    Queue = NodeQueue.BFS


foo = FooDFS()
foo.objective = max, FooNode.objective
foo.init(5)

bar = FooBFS()
bar.objective = min, FooNode.objective
bar.init(5)

if __name__ == "__main__":
    foo.run()

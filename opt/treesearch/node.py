class TreeNode(object):
    """
    Abstract base class for tree nodes used in tree search algorithms. Depending on the search
    algorithm and its configuration, some or all of the abstract methods declared here should be
    defined in subclasses. Below is an overview of the role of each method/operation:
        root(solver)         # create the starting point of the search
        copy()               # create an exact copy of a node
        release()            # release memory taken by a node
        branches()           # list of branching options available at a node
        apply(branch)        # modify a node (in-place) by following a given branch
        undo(branch)         # the opposite of apply()
        is_leaf()            # check whether a node is a leaf or not
        solution_and_meta()  # extract the solution data and metadata from a leaf node
        objective()          # compute the objective function value of a node
        bound()              # compute a bound on the objective function for a node
    Please refer to the documentation on these methods for more information on their role in the
    tree search algorithms, and what they should implement. Also remember to check the algorithm's
    documentation to find out which set of methods each specific algorithm uses.

    In addition to the methods above, the class should also define a 'sense' attribute, which
    specifies the sense (maximization or minimization) of the objective function.
    """
    __slots__ = ()

    @classmethod
    def root(cls, solver):
        """root() : solver -> TreeNode
        Create and return the starting point of the search. This method takes a reference to the
        solver as argument."""
        raise NotImplementedError()

    def copy(self):
        """copy() : void -> TreeNode
        Create a identical copy of this node."""
        raise NotImplementedError()

    def release(self):
        """release() : void -> object
        Called by MCTS after the node has been completely expanded. This can be used to release the
        memory used by the node, either fully (as in the default) by returning None, or partially
        by returning any object (including the node itself).
        """
        return None

    def branches(self):
        """branches() : void -> [branch]
                      | void -> [TreeNode]
        Create a list of branches available at a given node. The elements of the branch list
        should contain all the necessary information to apply a change to a node.
        Optionally, instead of returning a list of data to apply modifications to the node, this
        method may directly create and return a list of TreeNode objects already containing the
        corresponding modifications. In such case, the apply() method does not have to be defined,
        since it will not be used."""
        raise NotImplementedError()

    def apply(self, branch):
        """apply() : branch -> void
        Apply an *in-place* modification to a node. The argument to this method is a single element
        of the branch list returned by the branches() method."""
        raise NotImplementedError()

    def undo(self, branch):
        """undo() : branch -> void
        This is the opposite of apply(). It should reverse any modifications done by apply(), such
        that the following would result in no modification to the node
            node.apply(branch)
            node.undo(branch)
        """
        raise NotImplementedError()

    def is_leaf(self):
        """is_leaf() : void -> bool
        Return a boolean indicating whether this node is a leaf or not. The default behavior is
        always returning False, since the tree search solver can alternatively check if the
        branches() method returns an empty iterable, and deal with such cases as leaves. It is,
        however, advisable to provide an application-specific leaf check."""
        return False

    def solution_and_meta(self):
        """solution_and_meta() : void -> (object, dict)
        Return a Python object representing the solution data contained in a leaf node, plus a
        dictionary of metadata to be associated with the solution. The default behavior will return
        the node itself and an empty metadata dictionary."""
        return self, {}

    def objective(self):
        """objective() : void -> obj
        Compute and return the objective function value of a given leaf node."""
        raise NotImplementedError()

    """Optimization sense, i.e. defines how objective values compare to each other."""
    sense = None

    def bound(self):
        """bound() : void -> bound
        Compute and return a bound on the best objective function value (z) that can be obtained
        in a given subtree.  Note that returning a value which is not a real bound will cause
        incorrect pruning decisions in branch-and-bound algorithms."""
        raise NotImplementedError()

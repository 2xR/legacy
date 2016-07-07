from __future__ import absolute_import

from functools import partial
from utils.misc import max_elems
from utils.prettyrepr import prettify_class

from .relaxation import Relaxation
from .data import BranchingData


@prettify_class
class BranchingRule(object):
    """
    Base class for branching rules for **gurobi MIP models**.
    """
    def __init__(self, model=None):
        self.reset()
        if model is not None:
            self.init(model)

    def reset(self):
        self.relaxation = None

    def init(self, model):
        """Initialize the branching rule for the argument gurobi MIP model."""
        if self.relaxation is not None:
            raise Exception("duplicate attempt to initialize branching rule")
        self.relaxation = Relaxation(model)
        return self.root

    def root(self, model=None):
        """Creates the BranchingData object for the root node (i.e. containing an empty partial
        solution).  If a model is provided, the branching rule is init()ed with the argument."""
        if model is not None:
            self.init(model)
        return BranchingData(self, {})

    def branches(self, node, rng):
        """Given a node, selects a branching variable, branches on the selected variable (i.e.
        generates its children), and records the branching decision.  Returns a 2-tuple containing
        the variable that was branched on and a list with the two child BranchingData objects."""
        var_name = self.select_variable(node, rng)
        children = self.branch_on(var_name, node)
        self.record_branching(var_name, node, children)
        return var_name, children

    def select_variable(self, node, rng):
        """Pick a variable to branch on.  A variable is randomly selected from the set of variables
        with maximum branching score."""
        return rng.choice(self.branching_candidates(node))

    def branching_candidates(self, node):
        """Computes the set of variables with maximum branching score on the argument node."""
        return max_elems(node.fractional_vars, key=partial(self.branching_score, node=node))

    def branching_score(self, var_name, node):
        """Compute the score associated with branching on variable 'var_name' w.r.t. to the given
        node.  Variable with high branching score are preferred."""
        raise NotImplementedError()

    def branch_on(self, var_name, node):
        """Given a node and a variable, return the two branches."""
        return node.branch_on(var_name)

    def record_branching(self, var_name, parent, children):
        """Record any useful information about the most recent branching decision."""
        pass

    @staticmethod
    def merged_score(delta_obj1, delta_obj2, mu=1.0/6.0):
        """Given the variation in relaxation objective of two branches (corresponding to branching
        on a particular fractional variable), merge them into a single score.  'mu' is the weight
        given to the worse of the two branches.
        IMPORTANT: the objective deltas are converted into absolute values, since their magnitudes
        represent the degradation in objective value caused by rounding the variable (note that the
        objective value of the relaxation can only become worse or equal, never better, when the
        domain of a variable is reduced).  This way, the "better" branch is always the one with
        smaller degradation, independently of the optimization sense (min or max).  Another
        consequence is that the value returned by this method is always non-negative and can be
        safely used as the return value of the branching_score() method.
        NOTE: this method is not to be confused with branching_score(), which should compute a
        score given a node and a variable.  Instead of replacing branching_score(), this method
        should normally be used *by* it."""
        degradation1 = abs(delta_obj1)
        degradation2 = abs(delta_obj2)
        if degradation1 < degradation2:
            better = degradation1
            worse = degradation2
        else:
            better = degradation2
            worse = degradation1
        return (1 - mu) * better + mu * worse

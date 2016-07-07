from __future__ import absolute_import

from math import floor, ceil
from opt.gurobi import fractionality


class BranchingData(object):
    """
    This class encapsulates the node data relevant for the branching decision to be made, namely,
    the partial solution contained in the node (a {var_name: (lb, ub)} dictionary), the relaxation
    solution, the relaxation objective, and the set of fractional variables in the relaxation
    solution.
    """
    FRACTIONALITY_EPS = 1e-5

    __slots__ = ("rule",
                 "partial_sol",
                 "relax_sol",
                 "relax_obj",
                 "fractional_vars")

    def __init__(self, rule, partial_sol, relax_sol=None, relax_obj=None):
        if relax_sol is None:
            relax_sol, relax_obj = rule.relaxation.solve(partial_sol)
        self.rule = rule
        self.partial_sol = partial_sol
        self.relax_sol = relax_sol
        self.relax_obj = relax_obj
        if relax_sol is not None:
            eps = self.FRACTIONALITY_EPS
            self.fractional_vars = [var_name for var_name, var_value in relax_sol.iteritems()
                                    if fractionality(var_value) > eps]
        else:
            self.fractional_vars = []

    @property
    def is_feasible(self):
        return self.relax_sol is not None

    @property
    def is_infeasible(self):
        return self.relax_sol is None

    def branch_on(self, var_name):
        """Creates two BranchingData objects corresponding to branching down or up on the argument
        variable."""
        cls = type(self)
        down_bounds, up_bounds = self.branch_partial_sols(var_name)
        return cls(self.rule, down_bounds), cls(self.rule, up_bounds)

    def branch_partial_sols(self, var_name):
        """Given a variable name, creates the partial solutions (i.e. variable bounds dictionaries)
        of the two branches corresponding to branching from this node on the argument variable."""
        try:
            lb, ub = self.partial_sol[var_name]
        except KeyError:
            lb, ub = self.rule.relaxation.bounds[var_name]
        down_bounds = self.partial_sol.copy()
        down_bounds[var_name] = (lb, floor(self.relax_sol[var_name]))
        up_bounds = self.partial_sol.copy()
        up_bounds[var_name] = (ceil(self.relax_sol[var_name]), ub)
        return down_bounds, up_bounds

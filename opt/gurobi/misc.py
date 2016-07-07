"""
This module gathers some functions that are generally useful when working with gurobi models,
mostly integer or binary programs.
"""
from contextlib import contextmanager
from gurobipy import GRB


__all__ = ["check_unique_varnames", "set_params", "temporary_params",
           "clear_vars", "set_bounds", "fix_vars", "fix_var", "get_vars",
           "fractionality", "integrality", "var_fractionality", "var_integrality"]


def check_unique_varnames(model):
    unique = set()
    duplicate = set()
    for var in model.getVars():
        if var.var_name in unique:
            duplicate.add(var.var_name)
        else:
            unique.add(var.var_name)
    if len(duplicate) > 0:
        raise Exception("model contains variables with duplicate names: {!r}".format(duplicate))
    return True


def set_params(model, **params):
    for param, value in params.iteritems():
        setattr(model.params, param, value)


@contextmanager
def temporary_params(model, **temp_params):
    """Temporarily sets model parameters inside a 'with' statement, and restores the original
    parameter values before exiting the block."""
    orig_params = {param: getattr(model.params, param) for param in temp_params.iterkeys()}
    set_params(model, **temp_params)
    yield model
    set_params(model, **orig_params)


def clear_vars(model, vars=None, bounds={}, default_bounds=(0, GRB.INFINITY)):
    if vars is None:
        vars = model.getVars()
    if not isinstance(bounds, dict):
        bounds = dict(bounds)
    getVarByName = model.getVarByName
    for var in vars:
        if isinstance(var, basestring):
            var = getVarByName(var)
        lb, ub = (0, 1) if var.vtype == GRB.BINARY else bounds.get(var, default_bounds)
        var.lb = lb
        var.ub = ub
    model.update()


def set_bounds(model, bounds):
    if isinstance(bounds, dict):
        bounds = bounds.iteritems()
    getVarByName = model.getVarByName
    for var, (lb, ub) in bounds:
        if isinstance(var, basestring):
            var = getVarByName(var)
        var.lb = lb
        var.ub = ub
    model.update()


def fix_vars(model, sol):
    if isinstance(sol, dict):
        sol = sol.iteritems()
    getVarByName = model.getVarByName
    for var, val in sol:
        if isinstance(var, basestring):
            var = getVarByName(var)
        var.lb = val
        var.ub = val
    model.update()


def fix_var(model, var, val):
    if isinstance(var, basestring):
        var = model.getVarByName(var)
    var.lb = val
    var.ub = val
    model.update()


def get_vars(model, vars=None, varnames_as_keys=False):
    if vars is None:
        vars = model.getVars()
    getVarByName = model.getVarByName
    sol = []
    for var in vars:
        if isinstance(var, basestring):
            var = getVarByName(var)
        key = var.var_name if varnames_as_keys else var
        sol.append((key, var.x))
    return sol


def fractionality(x):
    """Given a value, return its distance from the nearest integer."""
    return 0.5 - abs(x % 1.0 - 0.5)


def integrality(x):
    """Given a value, return the distance between its fractional part and 0.5."""
    return abs(x % 1.0 - 0.5)


def var_fractionality(var):
    """The variable's distance from integer values."""
    return fractionality(var.x)


def var_integrality(var):
    """The distance between the variable's fractional part and 0.5."""
    return integrality(var.x)


# def convert_solution(sol, model):
#     """Given a solution for the main model, create an equivalent solution for the feasibility
#     relaxation of the main model, or vice-versa.  This is necessary because the two models use
#     different variable sets (although they're semantically the same)."""
#     var_map = model._var_map
#     converted = MBP_Solution()
#     for var, x in sol:
#         converted[var_map[var]] = x
#     return converted


# def feasibility_relaxation(model, relax_variable_bounds=False, relax_constraints=True):
#     """Create a feasibility relaxation of 'model'. The objective in this model is the minimization
#     of violations (variable bounds plus constraints). The parameters 'relax_variable_bounds' and
#     'relax_constraints' can be used to control what can be violated in the model.
#         NOTE: it is assumed that variable names are unique. This will produce incorrect results if
#         that is not the case.
#     """
#     feas_model = model.copy()
#     feas_model.feasRelaxS(0, False, relax_variable_bounds, relax_constraints)
#     feas_model._main_model = model
#     feas_model._bin_vars = bin_vars = []
#     feas_model._var_map = var_map = {}
#     model._feas_model = feas_model
#     model._var_map = var_rmap = {}
#     for var in model._bin_vars:
#         feas_var = feas_model.getVarByName(var.var_name)
#         bin_vars.append(feas_var)
#         var_map[var] = feas_var
#         var_rmap[feas_var] = var
#     return feas_model


# def probabilistic_rounding(model, relaxation_sol, partial_sol=None, theta=0.05, rng=random):
#     random = rng.random
#     sol = MBP_Solution() if partial_sol is None else partial_sol.copy()
#     i0 = len(sol) + len(relaxation_sol) - len(model._bin_vars)
#     assert 0 <= i0 < len(model._bin_vars)
#     for i in xrange(i0, len(relaxation_sol)):
#         var, x = relaxation_sol[i]
#         assert var not in sol
#         x = min(1.0-theta, max(theta, x))
#         sol[var] = 1 if random() < x else 0
#     assert len(sol) == len(model._bin_vars)
#     fix_vars(model, sol)
#     model.optimize()
#     obj = model.obj_val if model.status == GRB.status.OPTIMAL else None
#     return sol, obj


# def relax_and_fix(model, partial_sol=None, max_fractionality=0.1, max_batch_fixes=float("inf")):
#     integer_enough = lambda v: var_fractionality(v) <= max_fractionality
#     sol = MBP_Solution() if partial_sol is None else partial_sol.copy()
#     fix_vars(model, sol, clear=True)
#     free_vars = set(model._bin_vars)
#     free_vars.difference_update(sol)
#     while True:
#         model.optimize()
#         if model.status != GRB.status.OPTIMAL:
#             print "r&f: failed with {} fixed variables".format(len(sol))
#             return sol, None
#         print "r&f: z = {}".format(model.obj_val)
#         if len(free_vars) == 0:
#             break

#         new_fixes = filter(integer_enough, free_vars)
#         if len(new_fixes) == 0:
#             print "r&f: no 'integer enough' variables, choosing least fractional variable"
#             new_fixes = [max(free_vars, key=var_integrality)]
#         elif len(new_fixes) > max_batch_fixes:
#             if max_batch_fixes == 1:
#                 new_fixes = [max(new_fixes, key=var_integrality)]
#             else:
#                 new_fixes.sort(key=var_integrality, reverse=True)
#                 new_fixes = new_fixes[:max_batch_fixes]

#         print "r&f: fixing {} variables".format(len(new_fixes))
#         assert 0 < len(new_fixes) <= max_batch_fixes
#         for var in new_fixes:
#             x = round(var.x)
#             sol[var] = x
#             var.lb = x
#             var.ub = x
#         free_vars.difference_update(new_fixes)

#     return sol, model.obj_val


# def fix_and_bisect(model, relaxation_sol, partial_sol=None, rng=random):
#     sol, obj = probabilistic_rounding(model, relaxation_sol, partial_sol, rng)
#     if obj is not None:
#         return sol, obj
#     k = len(relaxation_sol) // 2
#     while k > 0:
#         print ("f&b: relaxation has {} int_vars; "
#                 "dropping last {} of {} int_vars".format(len(relaxation_sol), k, len(sol)))
#         for _ in xrange(k):
#             var, _ = sol.pop()
#             var.lb = 0
#             var.ub = 1
#         model.optimize()
#         if model.status == GRB.status.OPTIMAL:
#             print "f&b: relaxation okay. constructing new solution"
#             relaxation_sol = MBP_Solution.build_from(model, exclude=sol)
#             assert set(relaxation_sol.keys()) & set(sol.keys()) == set()
#             assert set(relaxation_sol.keys()) | set(sol.keys()) == set(model._bin_vars)
#             sol, obj = probabilistic_rounding(model, relaxation_sol, sol, rng)
#             if obj is not None:
#                 print "f&b: feasible solution found!"
#                 return sol, obj
#             print "f&b: solution is infeasible"
#             k = len(relaxation_sol) // 2
#         else:
#             print "f&b: relaxation failed."
#             k //= 2
#     print "f&b: no feasible solution found"
#     return sol, None


# def feasibility_pump(model, dist_model, partial_sol=None, rng=random, EPS=1e-5):
#     clear_vars(model)
#     if partial_sol is not None:
#         fix_vars(model, partial_sol)
#     model.optimize()
#     if model.status != GRB.status.OPTIMAL:
#         raise Exception("initial relaxation is infeasible")
#     sol = MBP_Solution.build_from(model)
#     if sol.is_integral():
#         return sol, model.obj_val

#     sol = convert_solution(sol, dist_model)
#     int_sol = sol.rounded_to_integer()
#     distance = sol.l1_distance(int_sol)
#     while distance > EPS:
#         fix_vars(dist_model, int_sol)
#         dist_model.optimize()
#         assert dist_model.status == GRB.status.OPTIMAL
#         distance = dist_model.obj_val
#         sol = MBP_Solution.build_from(dist_model)
#         int_sol = sol.rounded_to_integer()
#         distance = sol.l1_distance(int_sol)

from gurobipy import GRB, GurobiError
from opt.gurobi.misc import check_unique_varnames


class Relaxation(object):
    def __init__(self, model):
        if not model.is_mip:
            raise ValueError("argument model is not a MIP")
        check_unique_varnames(model)
        self.model = model.relax()
        self.model.params.OutputFlag = 0
        self.vars = {v.var_name for v in model.getVars() if v.vtype in (GRB.INTEGER, GRB.BINARY)}
        self.bounds = self.get_bounds()

    def get_bounds(self):
        """Gets the bounds for integer and binary variables currently in effect in the relaxation
        model."""
        get_var = self.model.getVarByName
        bounds = {}
        for var_name in self.vars:
            var = get_var(var_name)
            bounds[var_name] = (var.lb, var.ub)
        return bounds

    def set_bounds(self, var_bounds):
        """Sets lower and upper bounds on (originally) integer variables.  Any bounds that are
        provided by the argument dictionary default to the model's original bounds."""
        get_var = self.model.getVarByName
        for var_name, (orig_lb, orig_ub) in self.bounds.iteritems():
            try:
                lb, ub = var_bounds[var_name]
            except KeyError:
                lb, ub = orig_lb, orig_ub
            var = get_var(var_name)
            var.lb = lb
            var.ub = ub
        self.model.update()

    def solve(self, var_bounds):
        """This method solves a linear relaxation w.r.t. the argument partial solution (i.e. a
        {var_name: (lb, ub)} dictionary) and returns a 2-tuple (relax_sol, relax_obj) if the
        relaxation is feasible, or (None, None) otherwise."""
        self.set_bounds(var_bounds)
        self.model.optimize()
        return self.get_solution()

    def get_solution(self):
        """Returns a 2-tuple (relax_sol, relax_obj) if the solved relaxation is feasible, or
        (None, None) otherwise."""
        try:
            obj = self.model.obj_val
        except GurobiError:
            return None, None
        else:
            get_var = self.model.getVarByName
            sol = {var_name: get_var(var_name).x for var_name in self.vars}
        return sol, obj

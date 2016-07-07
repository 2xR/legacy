from utils import attr
from utils.misc import INF, max_elems
from utils.namespace import Namespace
from utils.timeseries import TimeSeries
from utils.prettyrepr import prettify_class

from opt.infeasible import Infeasible


@prettify_class
class Solution(object):
    """
    This class is meant as a standard container for solution data of any optimization problem.
    It contains only an objective value, the actual solution data, and a metadata namespace
    containing information such as the cpu time, solver iteration, etc.
    """
    def __init__(self, data, value, **meta):
        self.data = data
        self.value = value
        self.meta = Namespace(meta)

    def __info__(self):
        return "value={!r}".format(self.value)

    @property
    def is_feasible(self):
        return not isinstance(self.value, Infeasible)

    @property
    def is_infeasible(self):
        return isinstance(self.value, Infeasible)


class SolutionList(list):
    """
    The SolutionList class provides an easy standard way to record solutions found by solvers
    and keep track of best/worst feasible and least/most infeasible solutions and solution values.
    This class also provides convenience methods to plot time series of the objective function
    value of the solutions.
    A solution list is associated with a solver: it uses some of the solver's attributes and
    methods to compute missing information (objective value and cpu time). This also updates the
    solver's incumbent value when a new best feasible solution is found.
    """
    def __init__(self, solver):
        list.__init__(self)
        self.solver = solver
        self.checked_sol = None         # temporarily stores the solution being checked
        self.checked_obj = None         # same as checked_sol, but for objective value
        self.feas_count = None          # number of feasible solutions in the list
        self.infeas_count = None        # number of infeasible solutions in the list
        self.best_feas_value = None     # best feasible value found so far
        self.worst_feas_value = None    # worst feasible value found so far
        self.least_infeas_value = None  # least infeasible value found so far
        self.most_infeas_value = None   # most infeasible value found so far
        self.best_value = None          # best value so far (best feasible or least infeasible)
        self.clear()
        solver.channel.listen(solver.SIGNALS.SOLVER_INITIALIZED, self.init)

    def clear(self):
        """Remove all solutions from the list."""
        del self[:]
        self.checked_sol = None
        self.checked_obj = None
        self.feas_count = 0
        self.infeas_count = 0
        self.best_feas_value = None
        self.worst_feas_value = None
        self.least_infeas_value = INF
        self.most_infeas_value = 0.0
        self.best_value = Infeasible(INF)

    reset = clear

    def init(self):
        """These two attributes can only be initialized once the solver is in the 'initialized'
        state, otherwise the solver's sense may be undefined."""
        self.best_feas_value = self.solver.sense.worst_value
        self.worst_feas_value = self.solver.sense.best_value

    def best(self):
        """Returns the best solution in the list, or None if the list is empty."""
        if len(self) == 0:
            return None
        return max_elems(self, key=attr.getter("value"), gt=self.solver.sense.is_better)[0]

    def check(self, sol_container, value=None, **meta):
        """Check a given solution's objective function value. If the value is better/worse than
        the current best/worst feasible or infeasible values, the solution is added to the list.
        This method returns the new Solution object or None."""
        solver = self.solver
        if value is None:
            value = solver.objective(sol_container)
        self.checked_sol = sol_container
        self.checked_obj = value
        solver.channel.emit(solver.SIGNALS.CHECKING_SOLUTION)
        if isinstance(value, Infeasible):
            if value < self.least_infeas_value or value > self.most_infeas_value:
                return self.append(sol_container, value, **meta)
        else:
            is_better = solver.sense.is_better
            if is_better(value, self.best_feas_value) or is_better(self.worst_feas_value, value):
                return self.append(sol_container, value, **meta)
        if value == self.best_value:
            solver.channel.emit(solver.SIGNALS.BEST_SOL_ALTERNATIVE)
        return None

    def append(self, sol_container, value=None, **meta):
        """Creates a new solution and appends it to the solution list.  The solver's incumbent
        value is updated if necessary. The new Solution object is returned."""
        solver = self.solver
        if value is None:
            value = solver.objective(sol_container)
        self._update_stats(value)
        sol_data, sol_meta = solver._extract_solution_and_meta(sol_container)
        sol = Solution(sol_data, value)
        sol.meta.update(solver.meta)
        sol.meta.update(sol_meta)
        sol.meta.update(meta)
        sol.meta.setdefault("cpu", solver.cpu.total)
        sol.meta.setdefault("iteration", solver.iters.total+1)
        solver.channel.emit(solver.SIGNALS.SOLUTION_ADDED)
        list.append(self, sol)
        return sol

    add = append

    def _update_stats(self, value):
        """Updates the solution list's statistics with the value of a solution that is being
        added to the list.  Updated stats include (in)feasible solution counts, best/worst
        feasible values, least/most infeasible values, and best overall value."""
        solver = self.solver
        is_better = solver.sense.is_better
        if isinstance(value, Infeasible):
            self.infeas_count += 1
            if value < self.least_infeas_value:
                self.least_infeas_value = value
                solver.channel.emit(solver.SIGNALS.LEAST_INFEAS_VALUE_CHANGED)
            if value > self.most_infeas_value:
                self.most_infeas_value = value
                solver.channel.emit(solver.SIGNALS.MOST_INFEAS_VALUE_CHANGED)
        else:
            self.feas_count += 1
            if is_better(value, self.best_feas_value):
                self.best_feas_value = value
                solver.channel.emit(solver.SIGNALS.BEST_FEAS_VALUE_CHANGED)
            if is_better(self.worst_feas_value, value):
                self.worst_feas_value = value
                solver.channel.emit(solver.SIGNALS.WORST_FEAS_VALUE_CHANGED)
        if is_better(value, self.best_value):
            self.best_value = value
            solver.channel.emit(solver.SIGNALS.BEST_SOL_VALUE_CHANGED)
        if is_better(value, solver.incumbent):
            solver.incumbent = value

    # ------------------------------------------------------------------------------
    @staticmethod
    def make_tseries(solutions, extend_to=None):
        """Given an iterable of solutions, creates a time series of objective function values
        over cpu time.  If 'extend_to' is not None, the time series' last value is repeated at
        t = 'extend_to'."""
        tseries = TimeSeries.from_iterable((sol.meta.cpu, sol.value) for sol in solutions)
        if extend_to is not None and extend_to > tseries.time:
            tseries.append(extend_to, tseries.value)
        return tseries

    def plot(self, axes=None, seqs=["best_feas_seq"],
             extend_to=None, filename=None, dpi=300, **kwargs):
        """Build and display (or save) a plot showing the solutions' objective value over time.
        Note that this requires CPU time to be recorded. If filename is None, the plot is
        displayed to the screen, otherwise it is saved to the specified file. The filename
        extension will determine the format of the output file (e.g. pdf, eps, png, jpg)."""
        if extend_to is None:
            extend_to = self.solver.cpu.total
        for seq in seqs:
            seq = getattr(self, seq)
            tseries = SolutionList.make_tseries(seq(), extend_to=extend_to)
            axes = tseries.plot(axes=axes, xlabel="CPU time (s)", ylabel="Objective",
                                filename=filename, dpi=dpi, **kwargs)
        return axes

    def best_feas_seq(self):
        """Produces a sequence of solutions that caused the best feasible solution value to be
        updated."""
        is_better = self.solver.sense.is_better
        best = self.solver.sense.worst_value
        for sol in self:
            if sol.is_feasible and is_better(sol.value, best):
                best = sol.value
                yield sol

    def worst_feas_seq(self):
        """Produces a sequence of solutions that caused the worst feasible solution value to be
        updated."""
        is_better = self.solver.sense.is_better
        worst = self.solver.sense.best_value
        for sol in self:
            if sol.is_feasible and is_better(worst, sol.value):
                worst = sol.value
                yield sol

    def least_infeas_seq(self):
        """Produces a sequence of solutions that caused the least infeasible solution value to be
        updated."""
        best = INF
        for sol in self:
            if sol.is_infeasible and sol.value < best:
                best = sol.value
                yield sol

    def most_infeas_seq(self):
        """Produces a sequence of solutions that caused the most infeasible solution value to be
        updated."""
        worst = 0.0
        for sol in self:
            if sol.is_infeasible and sol.value > worst:
                worst = sol.value
                yield sol

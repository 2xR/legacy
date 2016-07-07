from time import time

from utils.params import Param as BaseParam
from utils.interval import Interval
from utils.misc import INF, UNDEF

from .plugins.limits import Limit


class Param(BaseParam):
    """
    This param subclass simply logs all parameter changes to the solver's info stream. (inspired
    by gurobi).  When the solver is reset, parameters that have 'reset_with_solver' equal to True
    are reset to their default values.
    """
    reset_with_solver = False

    def copy(self, **overrides):
        overrides.setdefault("reset_with_solver", self.reset_with_solver)
        return BaseParam.copy(self, **overrides)

    def on_solver_uninitialized(self, paramset):
        if self.reset_with_solver:
            self.reset(paramset)

    def _set(self, paramset, new_value):
        solver = paramset.owner
        if self in paramset.value_of:
            old_value = self.get(paramset)
            solver.log.debug("parameter changed <{!r}> {!r} -> {!r}",
                             self.name, old_value, new_value)
        else:
            solver.log.debug("parameter initialized <{!r}> := {!r}",
                             self.name, new_value)
        BaseParam._set(self, paramset, new_value)


class ParamSet(BaseParam.Set):
    def __init__(self, solver, **params):
        BaseParam.Set.__init__(self, solver, **params)
        solver.channel.listen(solver.SIGNALS.SOLVER_UNINITIALIZED, self.on_solver_uninitialized)

    def on_solver_uninitialized(self):
        for param in self.__params__:
            param.on_solver_uninitialized(self)

    # ------------------------------------------------------------------------------
    cpu_limit = Param(description="maximum run time allowed",
                      options="a value between 0 and inf",
                      domain=Interval(0, INF),
                      default=INF)
    cpu_limit.reset_with_solver = True

    @cpu_limit.setter
    def cpu_limit(self, limit):
        solver = self.owner
        solver.limits.update([Limit.Cpu.abs(limit)])

    @cpu_limit.adapter
    def cpu_limit(self, limit):
        return float(limit)

    # --------------------------------------------------------------------------
    iter_limit = Param(description="maximum number of iterations allowed",
                       options="a value between 0 and inf",
                       domain=Interval(0, INF),
                       default=INF)
    iter_limit.reset_with_solver = True

    @iter_limit.setter
    def iter_limit(self, limit):
        solver = self.owner
        solver.limits.update([Limit.Iters.abs(limit)])

    @iter_limit.adapter
    def iter_limit(self, limit):
        return float(limit)

    # --------------------------------------------------------------------------
    verbosity = Param(description="defines how much output is displayed by the solver",
                      options="[q]uiet (0), [n]ormal (1), or [v]erbose (2)",
                      domain=("quiet", "normal", "verbose"),
                      default="normal")

    @verbosity.adapter
    def verbosity(self, level):
        if isinstance(level, int):
            return type(self).verbosity.domain[level]
        level = level.strip().lower()
        if level in ("0", "q"):
            return "quiet"
        elif level in ("1", "n"):
            return "normal"
        elif level in ("2", "v"):
            return "verbose"
        else:
            return level

    @verbosity.setter
    def verbosity(self, level):
        solver = self.owner
        if level == "quiet":
            # disable everything except the error stream
            solver.log.disable()
            solver.log.error.enable()
        elif level == "normal":
            # enable everything except the debug stream
            solver.log.enable()
            solver.log.debug.disable()
        else:
            # enable everything
            solver.log.enable()

    # --------------------------------------------------------------------------
    seed = Param(description="the seed used by the random number generator",
                 options="anything goes, as long as it is hashable",
                 default=UNDEF)

    @seed.setter
    def seed(self, value):
        solver = self.owner
        solver.meta.seed = value
        solver.rng.seed(value)

    @seed.adapter
    def seed(self, value):
        if value in (UNDEF, None):
            return int(time() * 1000)
        return value if isinstance(value, int) else hash(value)

    # --------------------------------------------------------------------------
    instance_loader = Param(description="function used to load an instance by name",
                            options="a callable or None",
                            default=UNDEF)

    @instance_loader.getter
    def instance_loader(self):
        solver = self.owner
        return solver.instance_loader

    @instance_loader.setter
    def instance_loader(self, loader):
        solver = self.owner
        solver.instance_loader = loader

    @instance_loader.adapter
    def instance_loader(self, loader):
        if loader is None:
            return None
        if loader is UNDEF:
            return self.owner.instance_loader
        if callable(loader):
            return loader
        raise TypeError("instance loader should be callable or None")

    # --------------------------------------------------------------------------
    cutoff = Param(description="objective cutoff",
                   default=None)
    cutoff.reset_with_solver = True

    @cutoff.adapter
    def cutoff(self, value):
        return value if value is None else float(value)

    @cutoff.setter
    def cutoff(self, value):
        solver = self.owner
        try:
            listener = self.__cutoff_listener
        except AttributeError:
            listener = solver.channel.listen(solver.SIGNALS.SOLVER_INITIALIZED, callback=None)
            self.__cutoff_listener = listener

        if value is None:
            listener.callback = None
            listener.stop()
        else:
            def apply_cutoff():
                if solver.sense.is_better(value, solver.incumbent):
                    solver.incumbent = value

            if solver.state in (solver.STATE.BOOTSTRAPPED,
                                solver.STATE.RUNNING,
                                solver.STATE.PAUSED):
                apply_cutoff()
                listener.callback = None
                listener.stop()
            else:
                listener.callback = apply_cutoff
                listener.start()


Param.Set = ParamSet

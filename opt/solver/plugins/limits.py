from utils.misc import INF
from utils.prettyrepr import prettify_class

from .plugin import Plugin
from ..signals import SIGNALS
from ..statemachine import ACTION


class Limit(Plugin):
    """
    Each of these plugins adds an interrupt to the solver when a particular limit is reached,
    e.g. cpu time, iterations, solutions, etc.  In addition to interrupting the solver, a limit
    may emit a signal on the solver's channel.  Limits may be passed to the solver's run() method,
    and are uninstalled and discarded when the solver is run() again with new limits.
    """
    direction = +1

    def __init__(self, abs=None, rel=None):
        Plugin.__init__(self)
        if abs is None:
            abs = INF * self.direction
        if rel is None:
            rel = INF * self.direction
        self.abs = abs
        self.rel = rel
        self.limit = None

    def __info__(self):
        return ("dir={:+d}, abs={}, rel={}, lim={}, curr={}"
                .format(self.direction, self.abs, self.rel, self.limit, self.get_value()))

    @classmethod
    def abs(cls, abs):
        return cls(abs=abs)

    @classmethod
    def rel(cls, rel):
        return cls(rel=rel)

    activation_action = ACTION.PAUSE
    activation_signal = None

    @property
    def activation_message(self):
        comparator = ">=" if self.direction > 0 else "<="
        return "{} reached ({} {} {})".format(type(self).__name__, self.get_value(),
                                              comparator, self.limit)

    def install(self, solver):
        Plugin.install(self, solver)
        tighter_of = min if self.direction > 0 else max
        self.limit = tighter_of(self.abs, self.rel + self.get_value())

    def check(self):
        direction = self.direction
        if self.get_value() * direction >= self.limit * direction:
            if self.activation_signal is not None:
                self.solver.channel.emit(self.activation_signal)
            self.solver.interrupts.add(self.activation_message, self.activation_action)

    def get_value(self):
        raise NotImplementedError()


class CpuLimit(Limit):
    signal_map = {SIGNALS.ITERATION_FINISHED: "check"}
    activation_signal = SIGNALS.CPU_LIMIT_REACHED

    def install(self, solver):
        Limit.install(self, solver)
        solver.cpu.limit = self.limit

    def get_value(self):
        return self.solver.cpu.total


class ItersLimit(Limit):
    signal_map = {SIGNALS.ITERATION_FINISHED: "check"}
    activation_signal = SIGNALS.ITERATION_LIMIT_REACHED

    def install(self, solver):
        Limit.install(self, solver)
        solver.iters.limit = self.limit

    def get_value(self):
        return self.solver.iters.total


class FeasSolsLimit(Limit):
    signal_map = {SIGNALS.SOLUTION_ADDED: "check"}
    activation_signal = SIGNALS.SOLUTION_LIMIT_REACHED

    def get_value(self):
        return self.solver.solutions.feas_count


class GapLimit(Limit):
    signal_map = {SIGNALS.GAP_CHANGED: "check"}
    activation_signal = SIGNALS.GAP_LIMIT_REACHED
    direction = -1

    def get_value(self):
        return self.solver.gap


def to_limit(value):
    """Coerce a value to a solver limit. If the argument is already a Limit object, it is
    returned unchanged, otherwise coercion is attempted:
        - an integer is coerced into a relative iteration limit
        - a float is coerced into a relative cpu limit
        - TypeError is raised for all other values
    """
    if isinstance(value, Limit):
        return value
    elif isinstance(value, int):
        return Limit.Iters(rel=value)
    elif isinstance(value, float):
        return Limit.Cpu(rel=value)
    else:
        raise TypeError("unable to coerce value to limit: {!r}".format(value))


@prettify_class
class LimitManager(object):
    """
    This object manages the limits imposed on a solver. Limits are special-purpose solver plugins
    that are used to interrupt the solver's main loop when specific conditions are met, such as
    the cpu time reaching a certain threshold. Instead of being managed by the solver's plugin
    manager like other "regular" plugins, these are managed separately because they are replaced
    frequently by new limits.
    """
    def __init__(self, solver):
        self.solver = solver
        self.limits = set()

    def __info__(self):
        return self.limits

    def __len__(self):
        return len(self.limits)

    def __iter__(self):
        return iter(self.limits)

    def clear(self):
        for limit in self.limits:
            limit.uninstall()
        self.limits.clear()

    reset = clear

    def add(self, limit):
        """Add a limit to the limit manager.  Non-limit arguments are coerced to limits using
        to_limit() (see docstring for more details)."""
        limit = to_limit(limit)
        if limit not in self.limits:
            self.limits.add(limit)
            limit.install(self.solver)
            return True
        return False

    def extend(self, limits):
        """Add several limits to the manager in one go."""
        for limit in limits:
            self.add(limit)

    def update(self, limits):
        """This method works like extend(), but instead of simply adding all limits, it discards
        old limits of the same type as any of the argument limits, e.g. if a cpu limit is passed
        in the argument list, all previous cpu limits (type must match exactly) are discarded and
        replaced by the new cpu limit."""
        # build a {cls: [limits]} mapping
        type_map = {}
        for limit in self.limits:
            cls = type(limit)
            try:
                type_map[cls].append(limit)
            except KeyError:
                type_map[cls] = [limit]
        # now we apply the new limits, removing any previous limits of the same type
        for limit in limits:
            limit = to_limit(limit)
            cls = type(limit)
            if cls in type_map:
                for prev_limit in type_map[cls]:
                    prev_limit.uninstall()
                    self.limits.remove(prev_limit)
            self.add(limit)
            type_map[cls] = [limit]

    def set(self, limits):
        """Completely replaces any previous limits with the argument limits."""
        self.clear()
        self.extend(limits)

    def check(self):
        """Check all solver limits."""
        for limit in self.limits:
            limit.check()


Limit.Cpu = CpuLimit
Limit.Iters = ItersLimit
Limit.FeasSols = FeasSolsLimit
Limit.Gap = GapLimit
Limit.Manager = LimitManager

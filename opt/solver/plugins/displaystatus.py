from utils.misc import INF

from .plugin import Plugin
from ..signals import SIGNALS


class DisplayStatus(Plugin):
    """
    This plugin displays a status line whenever progress is made by the solver, i.e. whenever the
    incumbent or the bound change.  It also displays a line every 'interval' seconds even if no
    progress was made by the solver.
    """
    listener_priority = INF
    signal_map = {SIGNALS.SOLVER_UNINITIALIZED: "reset",
                  SIGNALS.BOUND_CHANGED: "display",
                  SIGNALS.INCUMBENT_CHANGED: "display",
                  SIGNALS.ITERATION_FINISHED: "periodic",
                  SIGNALS.SOLVER_PAUSING: "display",
                  SIGNALS.SOLVER_FINISHING: "display"}

    def __init__(self, interval=5.0):
        Plugin.__init__(self)
        self.interval = interval
        self.last_display = 0.0

    def reset(self):
        self.last_display = 0.0

    def periodic(self):
        if self.solver.cpu.total - self.last_display >= self.interval:
            self.display()

    def display(self):
        self.solver.status.write()
        self.last_display = self.solver.cpu.total

from .plugin import Plugin
from ..signals import SIGNALS
from ..termination import TERMINATION


class CheckOptimality(Plugin):
    """
    This plugin activates every time the gap changes. If the gap becomes zero (within a given
    'tolerance'), the solver is interrupted because the optimal solution has been found.
    """
    signal_map = {SIGNALS.GAP_CHANGED: "check"}
    tolerance = 1e-6

    def check(self):
        solver = self.solver
        if solver.gap < self.tolerance and solver.termination is None:
            solver.termination = TERMINATION.OPTIMAL

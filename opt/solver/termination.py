from collections import namedtuple
from utils.namespace import Namespace

from .signals import SIGNALS


TerminationStatus = namedtuple("TerminationStatus", ["message", "signal"])
TERMINATION = Namespace(
    UNKNOWN=TerminationStatus(message="unknown termination status",
                              signal=SIGNALS.UNKNOWN_TERMINATION),
    OPTIMAL=TerminationStatus(message="optimal solution found",
                              signal=SIGNALS.OPTIMAL_SOLUTION),
    INFEASIBLE=TerminationStatus(message="unable to find feasible solutions",
                                 signal=SIGNALS.PROBLEM_INFEASIBLE))

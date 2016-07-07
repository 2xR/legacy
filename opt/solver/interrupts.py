from utils.prettyrepr import prettify_class

from .statemachine import ACTION


@prettify_class
class InterruptManager(object):
    """
    This object manages solver interrupts. It maintains a queue of interrupt messages and
    associated solver state transitions.
    """
    legal_actions = {None, ACTION.PAUSE, ACTION.FINISH}

    def __init__(self, solver):
        self.solver = solver
        self.messages = []
        self.actions = []

    def __info__(self):
        return self.messages

    def __len__(self):
        return len(self.messages)

    def __nonzero__(self):
        return len(self.messages) > 0

    def clear(self):
        del self.messages[:]
        del self.actions[:]

    reset = clear

    def append(self, message, action=None):
        """Add a new interrupt to the solver. 'message' should describe the reason for the
        interrupt, and 'action' should be a solver transition symbol, normally ACTION.PAUSE or
        ACTION.FINISH (defined in statemachine.py), but None is a possible value, meaning that
        no action should be taken for that interrupt.  Note that interrupt actions are only
        applied when the 'apply()' method is called."""
        if action not in self.legal_actions:
            raise ValueError("unrecognized interrupt action: {!r}".format(action))
        self.messages.append(message)
        self.actions.append(action)

    add = append

    def report(self):
        """Write all interrupt messages onto the solver's logger object."""
        info = self.solver.log.info
        for message in self.messages:
            info(message)

    def apply(self, report=True):
        """Apply all interrupt actions to the solver at once.  All actions are applied one after
        the other.  Interrupt actions should normally be either 'pause' or 'finish'.  If 'report'
        is True, interrupt messages are logged afterwards."""
        result = None
        for action in self.actions:
            if action is not None:
                result = self.solver.input(action)
        if report:
            self.report()
        return result

class Infeasible(float):
    """
    This simple class can be used to signal infeasible solutions.  Values can be distinguished
    from regular float by checking their type.  Solvers should act appropriately on infeasible
    values.  The magnitude of an infeasible value indicates the amount of constraint violations
    in the associated solution, therefore it is not allowed to have a non-positive value (otherwise
    the solution would be feasible).
    """
    __slots__ = ()

    def __init__(self, degree):
        float.__init__(self, degree)
        if self <= 0.0:
            raise ValueError("degree of infeasibility must be positive")

    def __repr__(self):
        return "{}({})".format(type(self).__name__, float.__repr__(self))

    def __eq__(self, other):
        return type(self) is type(other) and float.__eq__(self, other)

    def __ne__(self, other):
        return type(self) is not type(other) or float.__ne__(self, other)

    def __gt__(self, other):
        return type(self) is type(other) and float.__gt__(self, other)

    def __ge__(self, other):
        return type(self) is type(other) and float.__ge__(self, other)

    def __lt__(self, other):
        return type(self) is type(other) and float.__lt__(self, other)

    def __le__(self, other):
        return type(self) is type(other) and float.__le__(self, other)

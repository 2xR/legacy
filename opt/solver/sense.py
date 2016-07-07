import operator

from utils.prettyrepr import prettify_class
from utils.misc import INF, flat_iter

from opt.infeasible import Infeasible


@prettify_class
class OptimizationSense(object):
    """
    An optimization sense is used to indicate whether we're minimizing or maximizing some function.
    It provides a 'is_better(a, b)' boolean method that returns True if 'a' is better than 'b' in
    the given sense, and False otherwise.  This method also deals correctly with infeasible values.
    The functions 'operator.lt' and 'operator.gt' are used for minimization and maximization,
    respectively.
    Likewise, the objective sense also defines what is the best value in a list of values through
    its 'best_in(values)' method (based on is_better()).
    """
    __slots__ = ("name", "_is_better", "best_value", "worst_value")

    def __init__(self, name, is_better, best_value, worst_value):
        self.name = name
        self._is_better = is_better
        self.best_value = best_value
        self.worst_value = worst_value

    def __info__(self):
        return self.name

    def is_better(self, a, b):
        if isinstance(a, Infeasible):
            return isinstance(b, Infeasible) and a < b
        elif isinstance(b, Infeasible):
            return True
        else:
            return self._is_better(a, b)

    def is_worse(self, a, b):
        return self.is_better(b, a)

    def best_in(self, *values):
        values = flat_iter(values)
        try:
            best = values.next()
        except StopIteration:
            raise Exception("no values provided")
        is_better = self.is_better
        for value in values:
            if is_better(value, best):
                best = value
        return best

    def worst_in(self, *values):
        values = flat_iter(values)
        try:
            worst = values.next()
        except StopIteration:
            raise Exception("no values provided")
        is_better = self.is_better
        for value in values:
            if is_better(worst, value):
                worst = value
        return worst

    # ------------------------------------------------------------------------------
    MAPPING = {}

    @classmethod
    def register(cls, sense, *synonyms):
        cls.MAPPING.update((synonym, sense) for synonym in synonyms)

    @classmethod
    def get(cls, sense):
        if not isinstance(sense, OptimizationSense):
            if isinstance(sense, str):
                sense = sense.strip().lower()
            try:
                sense = cls.MAPPING[sense]
            except KeyError:
                raise ValueError("unrecognized optimization sense: {!r}".format(sense))
        return sense


MIN = OptimizationSense(name="min", is_better=operator.lt, best_value=-INF, worst_value=+INF)
MAX = OptimizationSense(name="max", is_better=operator.gt, best_value=+INF, worst_value=-INF)

OptimizationSense.register(MIN, min, "min", "minimize", "minimization", "<", operator.lt, -1)
OptimizationSense.register(MAX, max, "max", "maximize", "maximization", ">", operator.gt, +1)

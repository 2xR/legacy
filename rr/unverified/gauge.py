from utils.prettyrepr import prettify_class
from utils.misc import INF


@prettify_class
class Gauge(object):
    """A very simple gauge class that manages a single quantity and a limit. Has a useful property
    'remaining' which lets us know the difference between the limit and the current total."""
    __info_attrs__ = ("total", "limit")
    __slots__ = ("initial_value", "total", "limit")

    def __init__(self, initial_value=0, limit=INF):
        self.initial_value = initial_value
        self.total = initial_value
        self.limit = limit

    def reset(self, initial_value=None):
        if initial_value is not None:
            self.initial_value = initial_value
        self.total = self.initial_value
        self.limit = INF

    clear = reset

    @property
    def remaining(self):
        return self.limit - self.total

    def add(self, n=1):
        self.total += n

    def subtract(self, n=1):
        self.total -= n

    incr = add
    decr = sub = subtract

    def __iadd__(self, n):
        self.add(n)
        return self

    def __isub__(self, n):
        self.subtract(n)
        return self

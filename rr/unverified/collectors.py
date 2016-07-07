from utils.misc import NAN


class Average(object):
    __slots__ = ("total", "count")

    def __init__(self, init_value=None, init_weight=1.0):
        self.reset()
        if init_value is not None:
            self.collect(init_value, init_weight)

    def collect(self, value, weight=1.0):
        self.total += value * weight
        self.count += weight

    def reset(self):
        self.total = 0.0
        self.count = 0.0

    clear = reset

    @property
    def value(self):
        return NAN if self.count == 0.0 else self.total / self.count

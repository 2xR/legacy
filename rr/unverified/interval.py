from __future__ import absolute_import
from copy import deepcopy

from utils.sequence import SequenceLike
from utils.prettyrepr import prettify_class
from utils.misc import check_type


@prettify_class
class Interval(SequenceLike):
    """Represents an interval of real numbers."""
    __items__ = ("start", "end")
    __slots__ = ("_start", "_end", "__weakref__")

    def __init__(self, start, end, auto_sort=False):
        if start > end:
            if auto_sort:
                start, end = end, start
            else:
                raise ValueError("invalid interval bounds: start > end")
        self._start = start
        self._end = end

    def __info__(self):
        return "%s, %s" % (self._start, self._end)

    @classmethod
    def around(cls, midpoint, diameter):
        """Alternative constructor. Create an interval of given diameter around the specified
        midpoint."""
        if diameter < 0.0:
            raise ValueError("invalid interval diameter: < 0")
        return cls(midpoint - diameter * 0.5, midpoint + diameter * 0.5)

    # --------------------------------------------------------------------------
    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        if start > self._end:
            raise ValueError("invalid interval start: > end")
        self._start = start

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, end):
        if end < self._start:
            raise ValueError("invalid interval end: > start")
        self._end = end

    @property
    def diameter(self):
        return self._end - self._start

    @diameter.setter
    def diameter(self, diameter):
        if diameter < 0.0:
            raise ValueError("invalid interval diameter: < 0")
        radius = diameter * 0.5
        midpoint = self.midpoint
        self._start = midpoint - radius
        self._end = midpoint + radius

    # other commonly used names for diameter
    size = width = length = diameter

    @property
    def radius(self):
        return self.diameter * 0.5

    @radius.setter
    def radius(self, radius):
        self.diameter = radius * 2.0

    @property
    def midpoint(self):
        return (self._start + self._end) * 0.5

    @midpoint.setter
    def midpoint(self, midpoint):
        self.shift(midpoint - self.midpoint)

    center = midpoint

    def stretch(self, ratio, pivot=None):
        if ratio < 0.0:
            raise ValueError("invalid interval stretch ratio: < 0")
        if pivot is None:
            pivot = self.midpoint
        self._start = pivot - (pivot - self._start) * ratio
        self._end = pivot - (pivot - self._end) * ratio

    def include(self, *values):
        """Extend (if necessary) the interval in order to include the argument values."""
        min_value = min(values)
        max_value = max(values)
        if min_value < self._start:
            self._start = min_value
            return True
        elif max_value > self._end:
            self._end = max_value
            return True
        return False

    def contains(self, other):
        if isinstance(other, Interval):
            return self._start <= other._start and other._end <= self._end
        return self._start <= other <= self._end

    __contains__ = contains

    def intersects(self, interval):
        check_type(interval, Interval)
        return self._start <= interval._end and self._end >= interval._start

    def isdisjoint(self, interval):
        return not self.intersects(interval)

    def intersection(self, interval):
        if not self.intersects(interval):
            return None
        start = max(self._start, interval._start)
        end = min(self._end, interval._end)
        return type(self)(start, end)

    __and__ = intersection

    def shift(self, delta):
        self._start += delta
        self._end += delta
        return self

    __iadd__ = shift

    def __isub__(self, value):
        return self.shift(-value)

    def __add__(self, value):
        return deepcopy(self).shift(value)

    def __sub__(self, value):
        return deepcopy(self).shift(-value)

    def __eq__(self, interval):
        return (isinstance(interval, Interval) and
                self._start == interval._start and
                self._end == interval._end)

    def __ne__(self, interval):
        return not self.__eq__(interval)

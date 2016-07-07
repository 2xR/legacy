from math import isnan
from copy import deepcopy

from utils.copy import blank_instance, fetch_copy
from utils.misc import NAN, check_type
from utils.plotter import get_plot_target
from utils.sequence import SequenceLike
from utils.approx import Approx

from geom2d.geometry import Geometry


class Segment(Geometry, SequenceLike):
    """Class representing arbitrary line segments. A line segment that is assumed to be immutable,
    that is, its attributes are not supposed to be modified after the constructor."""
    __slots__ = ("x0", "y0", "x1", "y1",
                 "x_min", "x_max", "y_min", "y_max",
                 "dx", "dy", "m", "b", "__weakref__")
    __items__ = ("p0", "p1")
    __info_attrs__ = ("p0", "p1", "m", "b")

    # parameter bounds for the parametric equation of the line
    t_min = 0.0
    t_max = 1.0

    def __init__(self, p0, p1):
        # anything that allows iteration and has two values can be passed as a point
        x0, y0 = p0
        x1, y1 = p1
        dx = x1 - x0
        dy = y1 - y0
        if dx == 0.0 and dy == 0.0:
            raise ValueError("coinciding points in %s definition" % type(self).__name__)
        # initialize properties directly, since __setattr__ prevents normal attribute assignment
        Segment.x0.__set__(self, x0)
        Segment.x1.__set__(self, x1)
        Segment.y0.__set__(self, y0)
        Segment.y1.__set__(self, y1)
        Segment.dx.__set__(self, dx)
        Segment.dy.__set__(self, dy)
        if x0 < x1:
            Segment.x_min.__set__(self, x0)
            Segment.x_max.__set__(self, x1)
        else:
            Segment.x_min.__set__(self, x1)
            Segment.x_max.__set__(self, x0)
        if y0 < y1:
            Segment.y_min.__set__(self, y0)
            Segment.y_max.__set__(self, y1)
        else:
            Segment.y_min.__set__(self, y1)
            Segment.y_max.__set__(self, y0)
        if dx == 0.0:
            Segment.m.__set__(self, NAN)
            Segment.b.__set__(self, NAN)
        else:
            m = float(dy) / dx
            Segment.m.__set__(self, m)
            Segment.b.__set__(self, y0 - m * x0)

    def __setattr__(self, attr, value):
        """Prevent assignment to the attributes of a Segment object, making it as immutable
        as is possible in Python."""
        raise AttributeError("%s object is immutable" % (type(self).__name__,))

    def __delattr__(self, attr):
        """Likewise, prevent attribute deletion."""
        raise AttributeError("%s object is immutable" % (type(self).__name__,))

    # must implement copy methods because __setattr__
    # prevents the copy module from working normally
    def __copy__(self):
        clone = blank_instance(type(self))
        for attr in ("x0", "y0", "x1", "y1", "x_min", "x_max",
                     "y_min", "y_max", "dx", "dy", "m", "b"):
            prop = getattr(Segment, attr)
            prop.__set__(clone, getattr(self, attr))
        return clone

    def __deepcopy__(self, memo):
        clone = fetch_copy(self, memo)
        for attr in ("x0", "y0", "x1", "y1", "x_min", "x_max",
                     "y_min", "y_max", "dx", "dy", "m", "b"):
            prop = getattr(Segment, attr)
            prop.__set__(clone, deepcopy(getattr(self, attr), memo))
        return clone

    @property
    def p0(self):
        return (self.x0, self.y0)

    @property
    def p1(self):
        return (self.x1, self.y1)

    def x_at(self, y):
        m = self.m
        return NAN if m == 0.0 else (y - self.b) / m

    def y_at(self, x):
        return self.m * x + self.b

    def intersection(self, other):
        """Line intersection algorithm using Cramer's Rule. We put the two lines in parametric
        form and solve the system for the parameters 't' and 's' (the parameter in each line's
        parametric equation). This system of two equations is solved using Cramer's Rule.

            NOTE: this method will break when any of the values involved in the computation is too
        large (close to float/double overflow) and the internal computations result in an infinite
        determinant (i.e. float("inf")) for the original coefficient matrix ((a b) (c d)). If this
        determinant is infinite, the values of the parameters t and s will both be zero or NaN,
        leading to incorrect results."""
        check_type(other, Segment)
        # both the x and y ranges must overlap for an intersection to be possible
        if (self.x_min > other.x_max or self.x_max < other.x_min or
            self.y_min > other.y_max or self.y_max < other.y_min):
            return None
        # a, b, c and d are the coefficients of the matrix
        a = self.dx
        b = -other.dx
        c = self.dy
        d = -other.dy
        ad_bc = a*d - b*c
        # if the determinant is 0, the system is either incompatible or indeterminate
        if ad_bc == 0.0:
            return _parallel_intersection(self, other)
        # e and f are the rhs values of the system
        e = other.x0 - self.x0
        f = other.y0 - self.y0
        # compute the parameter t in this line's equation and check if it is within bounds
        t = float(e*d - b*f) / ad_bc
        cls = type(self)
        if not (cls.t_min <= t <= cls.t_max):
            return None
        # compute the parameter s in the other line's equation and check if it is within bounds
        s = float(a*f - e*c) / ad_bc
        cls = type(other)
        if not (cls.t_min <= s <= cls.t_max):
            return None
        # finally, we find the point of intersection by applying parameter t to this line
        x = self.x0 + self.dx * t
        y = self.y0 + self.dy * t
        _x = other.x0 + other.dx * s
        _y = other.y0 + other.dy * s
        assert x == Approx(_x) and y == Approx(_y)
        return (x, y)

    # --------------------------------------------------------------------------
    # Geometry interface
    def move(self, dx=0.0, dy=0.0):
        if dx != 0.0:
            Segment.x0.__set__(self, self.x0 + dx)
            Segment.x1.__set__(self, self.x1 + dx)
            Segment.x_min.__set__(self, self.x_min + dx)
            Segment.x_max.__set__(self, self.x_max + dx)
            Segment.b.__set__(self, self.b - self.m * dx)
        if dy != 0.0:
            Segment.y0.__set__(self, self.y0 + dy)
            Segment.y1.__set__(self, self.y1 + dy)
            Segment.y_min.__set__(self, self.y_min + dy)
            Segment.y_max.__set__(self, self.y_max + dy)
            Segment.b.__set__(self, self.b + dy)

    def scale(self, sx=1.0, sy=1.0, pivot=None):
        raise NotImplementedError("scale() unavailable for frozen segments")

    def rotate(self, a=0.0, pivot=None):
        raise NotImplementedError("rotate() unavailable for frozen segments")

    # --------------------------------------------------------------------------
    # Helper method to draw the segment into a plot target
    p0_marker = dict(linestyle="", marker="x", markeredgewidth=3, markeredgecolor="blue")
    p1_marker = dict(linestyle="", marker="x", markeredgewidth=3, markeredgecolor="blue")

    def draw(self, target=None, **kwargs):
        """Draw the segment in a plotter or axes."""
        axes = get_plot_target(target).get_axes()
        axes.plot([self.x0, self.x1], [self.y0, self.y1], **kwargs)
        if self.p0_marker:
            axes.plot([self.x0], [self.y0], **self.p0_marker)
        if self.p1_marker:
            axes.plot([self.x1], [self.y1], **self.p1_marker)
        return axes


def _parallel_intersection(AB, CD):
    """Assuming that segments AB and CD are parallel (i.e. they have the same slope), compute
    their intersection if it consists of a unique point. For an intersection to exist, the
    segments must be collinear and share a single point. If the segments are parallel but not
    collinear, no intersection exists and None is returned. Finally, if the segments are
    collinear and share infinitely many points, None is returned as well."""
    assert AB.m == CD.m or isnan(AB.m) and isnan(CD.m)
    if isnan(AB.m):  # vertical lines
        if AB.x0 == CD.x0:  # collinearity check
            y_min = max(AB.y_min, CD.y_min)
            y_max = min(AB.y_max, CD.y_max)
            if y_min == y_max:  # single point of intersection check
                return (AB.x0, y_min)
    else:  # horizontal or diagonal lines
        if AB.b == CD.b:  # collinearity check
            x_min = max(AB.x_min, CD.x_min)
            x_max = min(AB.x_max, CD.x_max)
            if x_min == x_max:  # single point of intersection check
                return (x_min, AB.y_at(x_min))
    return None

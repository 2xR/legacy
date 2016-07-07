from geom2d.segment import Segment
from utils.misc import INF


class Line(Segment):
    """A infinite line defined by p0 and p1."""
    __slots__ = ()

    # parameter bounds for the parametric equation of the line
    t_min = -INF
    t_max = +INF

    p0_marker = dict(Segment.p0_marker)
    p0_marker.update(marker="d", markeredgecolor="purple")
    p1_marker = dict(Segment.p1_marker)
    p1_marker.update(marker="d", markeredgecolor="purple")

    def __init__(self, p0, p1):
        Segment.__init__(self, p0, p1)
        if self.dx != 0.0:
            Segment.x_min.__set__(self, -INF)
            Segment.x_max.__set__(self, INF)
        if self.dy != 0.0:
            Segment.y_min.__set__(self, -INF)
            Segment.y_max.__set__(self, INF)

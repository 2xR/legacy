from geom2d.segment import Segment
from utils.misc import INF


class Ray(Segment):
    """A ray is a half-line starting at p0 and extending infinitely in the direction of p1."""
    __slots__ = ()
    
    # parameter bounds for the parametric equation of the line
    t_min = 0.0
    t_max = +INF
    
    p0_marker = dict(Segment.p0_marker)
    p0_marker.update(markeredgecolor="pink")
    p1_marker = dict(Segment.p1_marker)
    p1_marker.update(marker="d", markeredgecolor="pink")
    
    def __init__(self, p0, p1):
        Segment.__init__(self, p0, p1)
        if self.dx > 0.0:
            Segment.x_max.__set__(self, INF)
        elif self.dx < 0.0:
            Segment.x_min.__set__(self, -INF)
        if self.dy > 0.0:
            Segment.y_max.__set__(self, INF)
        elif self.dy < 0.0:
            Segment.y_min.__set__(self, -INF)
            

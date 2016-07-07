from utils.misc import solve_quadratic
from geom2d.shape import Shape
from geom2d.vector import Vector


class Circle(Shape):
    def __init__(self, center=(0, 0), radius=1.0):
        self.center = Vector(*center)
        self.radius = radius

    def __info__(self):
        return "c=%s, r=%s" % (self.center, self.radius)

    # --------------------------------------------------------------------------
    # Geometry interface
    def move(self, dx=0.0, dy=0.0):
        if dx == 0.0 and dy == 0.0:
            return
        self.center.move(dx, dy)

    def scale(self, factor, pivot=None):
        if factor == 1.0:
            return
        if pivot is not None:
            self.center.scale(factor, pivot)
        self.radius *= factor

    def rotate(self, alpha, pivot=None):
        if alpha == 0.0:
            return
        if pivot is not None:
            self.center.rotate(alpha, pivot)

    # --------------------------------------------------------------------------
    # Shape interface
    def contains_point(self, point):
        radius = self.radius
        delta = point - self.center
        return delta.squared_length <= radius * radius

    def segment_intersections(self, segment):
        points = []
        cx, cy = self.center
        r = self.radius
        m = segment.slope
        if m is None:  # vertical segment
            if cx - r <= segment.a.x <= cx + r:
                pass
        else:
            b = segment.y_at(0.0)
            A = 1 + m*m
            B = -2*cx + 2*m*b -2*m*cy
            C = cx*cx + cy*cy + b*b - r*r - 2*b*cy
            x0, x1 = solve_quadratic(A, B, C)
            xinterval = segment.xrange
            if x0 in xinterval:
                points.append(Vector(x0, segment.y_at(x0)))
            if x1 in xinterval:
                points.append(Vector(x1, segment.y_at(x1)))
        return points



##    def segment_intersects(self, segment):
##        return self.contains_point(self.segment_closest_point(segment))
##
##    def segment_closest_point(self, segment):
##        """Determine the point in the argument segment which is closest to the center of the
##        circle.
##        AB - segment endpoints
##        C - center of the circle
##        r - radius of the circle
##        projection - projection scalar (result of dot product)
##        """
##        AB = segment.b - segment.a
##        AB_length = AB.length
##        if AB_length == 0:
##            return segment.a
##        AC = self.center - segment.a
##        AB_unit = AB.copy()
##        AB_unit.length = 1
##        projection = AC.dot(AB_unit)
##        return segment.a + max(0.0, min(AB_length, projection)) * AB_unit



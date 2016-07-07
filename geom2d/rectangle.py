from geom2d.polygon import Polygon
from geom2d.vector import Vector


class Rectangle(Polygon):
    def __init__(self, center=(0, 0), width=1.0, height=1.0, angle=0.0):
        self.center = Vector(*center)
        self.width = width
        self.height = height
        self.angle = angle
        
    def __info__(self):
        return "c=%s, w=%s, h=%s, a=%s" % (self.center, self.width, self.height, self.angle)
        
    def relpoint(self, rel_x, rel_y):
        """Get the coordinates of a point relative to the center of the rectangle. 'rel_x' and 
        'rel_y' should vary between -0.5 and +0.5. Note that the point returned depends on the 
        location of the rectangle's center, its dimensions, and its angle (e.g. top-left may 
        actually be at the bottom-right if the angle is equal to pi)."""
        point = Vector(rel_x * self.width, rel_y * self.height)
        point.angle += self.angle
        point += self.center
        return point
        
    @property
    def size(self):
        return self.width, self.height
        
    @size.setter
    def size(self, size):
        self.width, self.height = size
        
    @property
    def bottom_left(self):
        return self.relpoint(-0.5, -0.5)
        
    @property
    def bottom_right(self):
        return self.relpoint(+0.5, -0.5)
        
    @property
    def top_left(self):
        return self.relpoint(-0.5, +0.5)
        
    @property
    def top_right(self):
        return self.relpoint(+0.5, +0.5)
        
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
        self.width *= factor
        self.height *= factor
        
    def rotate(self, alpha, pivot=None):
        if alpha == 0.0:
            return
        if pivot is not None:
            self.center.rotate(alpha, pivot)
        self.angle += alpha
        
    # --------------------------------------------------------------------------
    # Shape interface
    def contains_point(self, point):
        point = Vector(*point)
        point -= self.center
        point.angle -= self.angle
        point.x /= self.width
        point.y /= self.height
        return -0.5 <= point.x <= 0.5 and -0.5 <= point.y <= 0.5
        
    # --------------------------------------------------------------------------
    # Polygon interface
    def vertices(self):
        return (self.bottom_left, self.bottom_right, self.top_right, self.top_left)
        

from geom2d.shape import Shape
from geom2d.vector import Vector


class Triangle(Shape):
    def __init__(self, a, b, c):
        self.a = a if isinstance(a, Vector) else Vector(a[0], a[1])
        self.b = b if isinstance(b, Vector) else Vector(b[0], b[1])
        self.c = c if isinstance(c, Vector) else Vector(c[0], c[1])
        
    def __repr__(self):
        return "%s(%s, %s, %s)" % (type(self).__name__, self.a, self.b, self.c)
        
    @property
    def center(self):
        #|AD| = |BD|
        pass
        
        
    def move(self, dx=0.0, dy=0.0):
        if dx == 0.0 and dy == 0.0:
            return
        self.a.move(dx, dy)
        self.b.move(dx, dy)
        self.c.move(dx, dy)
        
    def rotate(self, alpha, pivot=None):
        if alpha == 0.0:
            return
        if pivot is None:
            pivot = self.center
        self.a.rotate(alpha, pivot)
        self.b.rotate(alpha, pivot)
        self.c.rotate(alpha, pivot)
        
    def scale(self, factor, pivot=None):
        if factor == 1.0:
            return
        if pivot is None:
            pivot = self.center
        self.a.scale(alpha, pivot)
        self.b.scale(alpha, pivot)
        self.c.scale(alpha, pivot)
        

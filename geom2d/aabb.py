from math import sqrt

from geom2d.polygon import Polygon
from geom2d.vector import Vector
from utils.misc import check_type


class AABB(Polygon):
    """Axis-aligned bounding box. This is used by the quadtree for simple preliminary collision 
    detection."""
    def __init__(self, xlimits=(0.0, 1.0), ylimits=(0.0, 1.0)):
        self.xmin, self.xmax = xlimits
        self.ymin, self.ymax = ylimits
        if self.xmin > self.xmax or self.ymin > self.ymax:
            raise ValueError("invalid limits for AABB")
            
    def __info__(self):
        return "x: [%s, %s] y: [%s, %s]" % (self.xmin, self.xmax, self.ymin, self.ymax)
        
    @property
    def xcenter(self):
        return (self.xmin + self.xmax) * 0.5
        
    @xcenter.setter
    def xcenter(self, x):
        self.move(dx=x-self.xcenter)
        
    @property
    def ycenter(self):
        return (self.ymin + self.ymax) * 0.5
        
    @ycenter.setter
    def ycenter(self, y):
        self.move(dy=y-self.ycenter)
        
    @property
    def center(self):
        return Vector(self.xcenter, self.ycenter)
        
    @center.setter
    def center(self, xy):
        x, y = xy
        self.move(dx=x-self.xcenter, dy=y-self.ycenter)
        
    @property
    def bottom_left(self):
        return Vector(self.xmin, self.ymin)
        
    @property
    def bottom_right(self):
        return Vector(self.xmax, self.ymin)
        
    @property
    def top_left(self):
        return Vector(self.xmin, self.ymax)
        
    @property
    def top_right(self):
        return Vector(self.xmax, self.ymax)
        
    @property
    def area(self):
        return self.width * self.height
        
    @area.setter
    def area(self, a):
        if a < 0.0:
            raise ValueError("area must be non-negative")
        w0, h0 = float(self.width), float(self.height)
        if w0 == 0.0 or h0 == 0.0:
            raise Exception("unable to set area of null AABB")
        h1 = sqrt(a * h0 / w0)
        w1 = w0 * h1 / h0
        self.width = w1
        self.height = h1
        
    @property
    def width(self):
        return self.xmax - self.xmin
        
    @width.setter
    def width(self, w):
        if w < 0.0:
            raise ValueError("width must be non-negative")
        x = self.xcenter
        self.xmin = x - w * 0.5
        self.xmax = x + w * 0.5
        
    @property
    def height(self):
        return self.ymax - self.ymin
        
    @height.setter
    def height(self, h):
        if h < 0.0:
            raise ValueError("height must be non-negative")
        y = self.ycenter
        self.ymin = y - h * 0.5
        self.ymax = y + h * 0.5
        
    # --------------------------------------------------------------------------
    # AABB specific stuff (functionality used by QuadTree)
    def contains(self, obj):
        """Return true if 'obj' is contained within this AABB. 'obj' may be either a point or 
        another AABB."""
        if isinstance(obj, AABB):
            return (self.xmin <= obj.xmin and 
                    self.xmax >= obj.xmax and
                    self.ymin <= obj.ymin and 
                    self.ymax >= obj.ymax)
        else:
            return self.contains_point(obj)
            
    def intersects(self, aabb):
        """Return True if this AABB intersects with the argument AABB."""
        check_type(aabb, AABB)
        return not (self.xmin > aabb.xmax or 
                    self.xmax < aabb.xmin or
                    self.ymin > aabb.ymax or 
                    self.ymax < aabb.ymin)
        
    def intersection(self, aabb):
        """If this AABB intersects with the argument AABB, returns a new AABB containing the area 
        of intersection between the two. None is returned if there is no intersection."""
        if not self.intersects(aabb):
            return None
        return type(self)(xlimits=(max(self.xmin, aabb.xmin), min(self.xmax, aabb.xmax)),
                          ylimits=(max(self.ymin, aabb.ymin), min(self.ymax, aabb.ymax)))
        
    def split(self):
        """Returns a 4-tuple containing AABB's dividing the area of this AABB into four quadrants 
        of equal size."""
        cls = type(self)
        x0, x1, x2 = self.xmin, self.xcenter, self.xmax
        y0, y1, y2 = self.ymin, self.ycenter, self.ymax
        return (cls((x0, x1), (y0, y1)),
                cls((x0, x1), (y1, y2)),
                cls((x1, x2), (y0, y1)),
                cls((x1, x2), (y1, y2)))
        
    # --------------------------------------------------------------------------
    # Geometry interface
    def move(self, dx=0.0, dy=0.0):
        """Change the position of the AABB without changing its dimensions."""
        if dx != 0.0:
            self.xmin += dx
            self.xmax += dx
        if dy != 0.0:
            self.ymin += dy
            self.ymax += dy
            
    def scale(self, factor, pivot=None):
        if factor == 1.0:
            return
        if pivot is not None:
            center = self.center
            center.scale(factor, pivot)
            self.center = center
        self.width *= factor
        self.height *= factor
        
    def rotate(self, alpha, pivot=None):
        """Rotation around a pivot will only rotate the location of the center of the AABB. The 
        AABB itself will remain aligned with the x- and y- axes, as its name cleverly indicates :)
        """
        if alpha == 0.0:
            return
        if pivot is not None:
            center = self.center
            center.rotate(alpha, pivot)
            self.center = center
            
    # --------------------------------------------------------------------------
    # Shape interface
    def contains_point(self, vector):
        x, y = vector
        return (self.xmin <= x <= self.xmax and
                self.ymin <= y <= self.ymax)
        
    def collides(self, obj):
        if isinstance(obj, AABB):
            return self.intersects(obj)
        return Polygon.collides(obj)
        
    # --------------------------------------------------------------------------
    # Polygon interface
    def vertices(self):
        return (self.bottom_left, self.bottom_right, self.top_right, self.top_left)
        

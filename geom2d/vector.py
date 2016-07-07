from math import pi, sin, cos, atan, atan2, sqrt, hypot
from contextlib import contextmanager
from utils.misc import INF, NAN
from utils.sequence import SequenceLike

from geom2d.geometry import Geometry


class Vector(Geometry, SequenceLike):
    """Simple class for vectors (or, equivalently, points) in 2D Euclidean space."""
    __slots__ = ("x", "y", "__weakref__")
    __items__ = ("x", "y")
    
    # --------------------------------------------------------------------------
    # Constructor and magic methods
    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)
        
    def __info__(self):
        return "%s, %s" % (self.x, self.y)
        
    def __eq__(self, v):
        return isinstance(v, Vector) and self.x == v.x and self.y == v.y
        
    def __ne__(self, v):
        return not self.__eq__(v)
        
    def __pos__(self):
        return type(self)(self.x, self.y)
        
    def __neg__(self):
        return self.__mul__(-1.0)
        
    def __iadd__(self, v):
        dx, dy = v
        self.x += dx
        self.y += dy
        return self
        
    def __add__(self, v):
        return self.__pos__().__iadd__(v)
        
    __radd__ = __add__
    
    def __isub__(self, v):
        dx, dy = v
        self.x -= dx
        self.y -= dy
        return self
        
    def __sub__(self, v):
        return self.__pos__().__isub__(v)
        
    def __rsub__(self, v):
        return self.__mul__(-1.0).__iadd__(v)
        
    def __imul__(self, n):
        self.x *= n
        self.y *= n
        return self
        
    def __mul__(self, n):
        return self.__pos__().__imul__(n)
        
    __rmul__ = __mul__
    
    def __idiv__(self, n):
        self.x /= n
        self.y /= n
        return self
        
    def __div__(self, n):
        return self.__pos__().__idiv__(n)
        
    def __rdiv__(self, other):
        return NotImplemented
        
    # --------------------------------------------------------------------------
    # Derived properties and other methods
    @property
    def length(self):
        return hypot(self.x, self.y)
        
    @length.setter
    def length(self, l):
        if self.x == 0.0 and self.y == 0.0:
            self.x = float(l)
        else:
            ratio = l / self.length
            self.x *= ratio
            self.y *= ratio
            
    l = length
    
    @property
    def squared_length(self):
        x = self.x
        y = self.y
        return x * x + y * y
        
    @squared_length.setter
    def squared_length(self, l2):
        self.length = sqrt(l2)
        
    l2 = squared_length
    
    @property
    def angle(self):
        return atan2(self.y, self.x)
        
    @angle.setter
    def angle(self, a):
        l = self.length
        if l > 0.0:
            self.x = l * cos(a)
            self.y = l * sin(a)
            
    a = angle
    
    @property
    def slope(self):
        """The slope of the vector, i.e. y/x. If the vector is vertical or null, the slope is 
        undefined (the constant float("nan") is used. Use math.isnan() to check for this, since 
        NAN always compares different from other values, including itself)."""
        x = self.x
        y = self.y
        return NAN if x == 0.0 else float(y) / x
        
    @slope.setter
    def slope(self, m):
        self.angle = atan(m)
        
    m = slope
    
    def dot(self, v):
        """Compute the dot product between two vectors."""
        x, y = v
        return self.x * x + self.y * y
        
    @contextmanager
    def pivoting_to(self, p):
        """This context manager sets a pivot for one or more operations on the vector. If the 
        argument pivot is None, the vector is left unchanged (this is actually equivalent to 
        pivoting to (0, 0), but more efficient since no operations are executed)."""
        if p is None:
            yield self
        else:
            self -= p
            yield self
            self += p
            
    # --------------------------------------------------------------------------
    # Geometry interface
    def move(self, dx=0.0, dy=0.0):
        """Move the vector by a specified delta."""
        if dx != 0.0: self.x += dx
        if dy != 0.0: self.y += dy
        
    def scale(self, sx=1.0, sy=1.0, pivot=None):
        """Scale the vector with respect to a specified pivot point (default pivot is (0, 0))."""
        if sx != 1.0 or sy != 1.0:
            with self.pivoting_to(pivot):
                if sx != 1.0: self.x *= sx
                if sy != 1.0: self.y *= sy
                
    def rotate(self, a=0.0, pivot=None):
        """Rotate the vector, i.e. add a delta (in radians) to its angle. A rotation pivot other 
        than (0, 0) may be specified by using the 'pivot' argument (which must be vector-like)."""
        if a != 0.0:
            with self.pivoting_to(pivot):
                self.angle += a
                
                

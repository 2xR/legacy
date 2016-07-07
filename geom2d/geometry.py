from abc import ABCMeta, abstractmethod
from utils.prettyrepr import prettify_class


@prettify_class
class Geometry(object):
    """Base class for geometric primitives. All primitives should support the basic operations:
    move, scale, and rotate."""
    __metaclass__ = ABCMeta
    __slots__ = ()
    
    @abstractmethod
    def move(self, dx=0.0, dy=0.0):
        raise NotImplementedError()
        
    @abstractmethod
    def scale(self, sx=1.0, sy=1.0, pivot=None):
        raise NotImplementedError()
        
    @abstractmethod
    def rotate(self, a=0.0, pivot=None):
        raise NotImplementedError()
        

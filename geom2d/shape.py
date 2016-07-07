from geom2d.geometry import Geometry


class Shape(Geometry):
    collision_function = dict()
    
    def contains_point(self, vector):
        raise NotImplementedError()
        
    def segment_intersections(self, segment):
        raise NotImplementedError()
        
    @staticmethod
    def add_collision_function(cls1, cls2, fnc):
        setattr(cls1, "collides_" + cls2.__name__.lower(), fnc)
        setattr(cls2, "collides_" + cls1.__name__.lower(), reversed_args(fnc))
        
    @classmethod
    def get_collision_function(cls, other_cls):
        for ancestor_cls in other_cls.mro():
            fnc = getattr(cls, "collides_" + ancestor_cls.__name__.lower(), None)
            if fnc is not None:
                return fnc
        raise Exception("unable to find collision function")
        
    def collides(self, obj):
        return self.get_collision_function(type(obj))(obj)
        
        
        
def aabb_circle_collision(aabb, circle):
    x0, x1 = aabb.xrange
    y0, y1 = aabb.yrange
    x = max(x0, min(x1, circle.center.x))
    y = max(y0, min(y1, circle.center.y))
    return circle.contains_point((x, y))
    
    
def circle_circle_collision(circle0, circle1):
    return (circle1.center - circle0.center).length < circle0.radius + circle1.radius
    
    

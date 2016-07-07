import random
from math import pi

from geom2d.vector import Vector
from utils.approx import Approx


def random_vector():
    x = random.uniform(0, 4)
    y = random.uniform(5, 9)
    return Vector(x, y)
    
    
def test_vector():
    for _ in xrange(1000):
        v = random_vector()
        x, y = v
        assert v + (2, 0) == Vector(x+2, y)
        assert v - (2, 0) == Vector(x-2, y)
        assert +v == Vector(x, y)
        assert -v == Vector(-x, -y)
        assert v * 2 == Vector(2*x, 2*y)
        assert v / 2 == Vector(x/2, y/2)
        
        v = Vector(1, 0)
        assert v.angle == 0
        v.angle = pi/2
        v.x, v.y = map(Approx, v)
        assert v == Vector(0, 1)
        v.length = 2
        v.x, v.y = map(Approx, v)
        assert v == Vector(0, 2)
        v.move(2, 2)
        assert v == Vector(2, 4)
        v.scale(2, 2, pivot=(1, 1))
        assert v == Vector(3, 7)
        v.rotate(pi/2, pivot=(3, 3))
        v.x, v.y = [Approx(n) for n in v]
        assert v == Vector(-1, 3)
        
        

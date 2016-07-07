from copy import deepcopy
from random import random
from utils.approx import Approx
from geom2d.segment import Segment


def test_intersection():
    for _ in xrange(10000):
        s0 = Segment((random(), random()), (random(), random()))
        s1 = Segment((random(), random()), (random(), random()))
        p = s0.intersection(s1)
        if p is not None:
            x = Approx(p[0])
            y = Approx(p[1])
            assert s0.x_min <= x <= s0.x_max
            assert s0.y_min <= y <= s0.y_max
            assert s1.x_min <= x <= s1.x_max
            assert s1.y_min <= y <= s1.y_max
            assert x == s0.x_at(y)
            assert y == s0.y_at(x)
            assert x == s1.x_at(y)
            assert y == s1.y_at(x)
            
            
def test_parallel_intersection():
    s0 = Segment((0, 0), (0, 1))
    for _ in xrange(100):
        # collinear, single intersection
        s1 = Segment((0, 1), (0, 2+random()))
        assert s0.intersection(s1) == (0, 1)
        
        # collinear, infinitely many intersections
        s2 = Segment((0, 0.5), (0, 2+random()))
        assert s0.intersection(s2) is None
        
        # parallel, not collinear
        s3 = deepcopy(s0)
        s3.move(random(), random())
        assert s0.intersection(s3) is None
        

import pytest
from random import uniform

from utils.interval import Interval


@pytest.fixture
def interval():
    return Interval(0, 1)


def test_constructor():
    with pytest.raises(ValueError):
        i = Interval(10, 0)
    s = uniform(0, 100)
    e = uniform(s, 200)
    i = Interval(s, e)
    assert tuple(i) == (s, e)


def test_around():
    i = Interval.around(0, diameter=5)
    assert i == Interval(-2.5, 2.5)


def test_shift(interval):
    s, e = interval
    for _ in xrange(100):
        x = uniform(0, 100)
        s += x
        e += x
        interval += x
        assert tuple(interval) == (s, e)


def test_intersection(interval):
    s0, e0 = interval
    for _ in xrange(100):
        s = uniform(-1.0, 0.0)
        e = uniform(s, 2.0)
        i = interval.intersection(Interval(s, e))
        if s > e0 or e < s0:
            assert i is None
        else:
            assert isinstance(i, Interval)
            assert i.start == max(s0, s)
            assert i.end == min(e0, e)



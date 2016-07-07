from utils import c3


def bases_getter(o):
    return o.__basedicts__


def kro_getter(o):
    try:
        return o.__kro__
    except AttributeError:
        return [o]


class chaindict(dict):
    """This dictionary subclass looks for missing keys in other dictionaries using the same
    inheritance mechanism as Python uses for classes."""
    def __init__(self, *bases, **kwargs):
        if not all(isinstance(base, dict) for base in bases):
            raise TypeError("chaindict bases must be dictionaries")
        dict.__init__(self, kwargs)
        self.__basedicts__ = list(bases)
        self.__kro__ = c3.linearization(self, bases_getter, kro_getter)

    def lookup(self, k):
        """Look up the value associated to key 'k' in this chaindict. The value may be obtained
        either directly from this object or through inheritance from another dictionary in the
        object's KRO."""
        for D in self.__kro__:
            try:
                return dict.__getitem__(D, k)
            except KeyError:
                pass
        raise KeyError("unable to find %r in %s" % (k, type(self).__name__))

    __getitem__ = lookup
    __setitem__ = dict.__setitem__
    __delitem__ = dict.__delitem__

    def whereis(self, k):
        """Find the first dictionary in this object's KRO where key 'k' is defined."""
        for D in self.__kro__:
            try:
                dict.__getitem__(D, k)
            except KeyError:
                pass
            else:
                return D
        raise KeyError("unable to find %r in %s" % (k, type(self).__name__))

    def snapshot(self):
        """Create a dictionary with all items in the chaindict plus all items inherited from its
        bases. Note that keys defined in multiple places will be associated to the value that
        appears first in the chaindict's KRO (same as Python's inheritance mechanism)."""
        S = {}
        for D in reversed(self.__kro__):
            S.update(D)
        return S


def _test():
    a = dict(a=1)
    b = dict(b=2)
    c = dict(c=3)
    d = chaindict(a, b, c, d=4)
    e = dict(e=5)
    f = chaindict(d, e, f=6)
    assert d.snapshot() == dict(a=1, b=2, c=3, d=4)
    assert f.snapshot() == dict(a=1, b=2, c=3, d=4, e=5, f=6)
    assert f.whereis("a") is a
    assert f.whereis("b") is b
    assert f.whereis("c") is c
    assert f.whereis("d") is d
    assert f.whereis("e") is e
    assert f.whereis("f") is f
    return d, f

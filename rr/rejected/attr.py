# REJECTED in favor of doubler.utils.operator (overlap in functionality, but operator offers more)
"""
Utility functions for attribute access and modification. Recommended use:
from utils import attr

foobar = attr.xget(obj, "foo.bar")
# is equivalent to
foobar = obj.foo.bar

"""


def getter(name):
    def attr_getter(obj):
        return getattr(obj, name)
    attr_getter.__name__ = "get_%s" % name
    return attr_getter


def setter(name):
    def attr_setter(obj, val):
        setattr(obj, name, val)
    attr_setter.__name__ = "set_%s" % name
    return attr_setter


def deleter(name):
    def attr_deleter(obj):
        delattr(obj, name)
    attr_deleter.__name__ = "del_%s" % name
    return attr_deleter


def xget(obj, location):
    attrs = location.split(".")
    for attr in attrs:
        obj = getattr(obj, attr)
    return obj


def xset(obj, location, value):
    attrs = location.split(".")
    for x in xrange(len(attrs) - 1):
        obj = getattr(obj, attrs[x])
    setattr(obj, attrs[-1], value)


def xdel(obj, location):
    attrs = location.split(".")
    for x in xrange(len(attrs) - 1):
        obj = getattr(obj, attrs[x])
    delattr(obj, attrs[-1])


def xgetter(location):
    def attr_xgetter(obj):
        return xget(obj, location)
    attr_xgetter.__name__ = "xget_%s" % location
    return attr_xgetter


def xsetter(location):
    def attr_xsetter(obj, val):
        xset(obj, location, val)
    attr_xsetter.__name__ = "xset_%s" % location
    return attr_xsetter


def xdeleter(location):
    def attr_xdeleter(obj):
        xdel(obj, location)
    attr_xdeleter.__name__ = "xdel_%s" % location
    return attr_xdeleter

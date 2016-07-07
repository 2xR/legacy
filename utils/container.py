"""
This module contains a set of simple classes that provide a nothing more than a __contains__()
method.  The classes can be combined together to create useful pseudo-containers defining
arbitrarily complex sets through conditions (e.g. isinstance() or a user-provided predicate)
instead of enumeration.  Obviously these pseudo-sets cannot be enumerated/iterated over, but
membership can be tested (usually efficiently) for any objects.
"""
from collections import Container as ContainerABC
from functools import partial
from utils.prettyrepr import prettify_class


@prettify_class
class ContainerBase(ContainerABC):
    __slots__ = ()

    def __contains__(self, item):
        raise NotImplementedError()


class Union(ContainerBase, list):
    __slots__ = ()

    def __init__(self, *subdomains):
        list.__init__(self, map(new, subdomains))

    def __info__(self):
        return list.__repr__(self)

    def __contains__(self, obj):
        return any(obj in subdomain for subdomain in self)


class Intersection(ContainerBase, list):
    __slots__ = ()

    def __init__(self, *subdomains):
        list.__init__(self, map(new, subdomains))

    def __info__(self):
        return list.__repr__(self)

    def __contains__(self, obj):
        return all(obj in subdomain for subdomain in self)


class Complement(ContainerBase):
    __slots__ = ("target",)

    def __init__(self, target):
        self.target = target

    def __info__(self):
        return self.target

    def __contains__(self, obj):
        return obj not in self.target


class IsInstance(ContainerBase):
    __slots__ = ("cls",)

    def __init__(self, cls):
        self.cls = cls

    def __info__(self):
        return self.cls

    def __contains__(self, obj):
        return isinstance(obj, self.cls)


class IsSubclass(ContainerBase):
    __slots__ = ("cls",)

    def __init__(self, cls):
        self.cls = cls

    def __info__(self):
        return self.cls

    def __contains__(self, cls):
        return issubclass(cls, self.cls)


class InContainer(ContainerBase):
    __slots__ = ("container",)

    def __init__(self, container):
        self.container = container

    def __info__(self):
        return self.container

    def __contains__(self, item):
        return item in self.container


class Predicate(ContainerBase, partial):
    __slots__ = ()
    __init__ = partial.__init__
    __contains__ = partial.__call__

    def __info__(self):
        args = ", ".join(map(repr, self.args))
        if len(self.args) > 0 and self.keywords is not None:
            args += ", "
        keywords = ("" if self.keywords is None else
                    ", ".join("{}={!r}".format(k, v) for k, v in self.keywords.iteritems()))
        return "{}({}{})".format(self.func.__name__, args, keywords)


def new(arg):
    if isinstance(arg, ContainerBase):
        return arg
    if (((isinstance(arg, type) or
          isinstance(arg, tuple) and
          all(isinstance(x, type) for x in arg)))):
        return IsInstance(arg)
    if isinstance(arg, ContainerABC):
        return InContainer(arg)
    if callable(arg):
        return Predicate(arg)
    raise Exception("unrecognized value for domain: {!r}".format(arg))


def or_op(a, b):
    return Union(a, b)


def and_op(a, b):
    return Intersection(a, b)


def not_op(a):
    return Complement(a)


ContainerBase.new = staticmethod(new)
ContainerBase.__or__ = ContainerBase.__ror__ = or_op
ContainerBase.__and__ = ContainerBase.__rand__ = and_op
ContainerBase.__invert__ = not_op
ContainerBase.IsInstance = IsInstance
ContainerBase.IsSubclass = IsSubclass
ContainerBase.InContainer = InContainer
ContainerBase.Predicate = Predicate
ContainerBase.Union = Union
ContainerBase.Intersection = Intersection
ContainerBase.Complement = Complement

del or_op
del and_op
del not_op

"""
class Person(object):
    parents = relations.One(backref=".Parents:children")
    couple = relations.One(backref=".Parents:father")
    father = property(lambda self: self.parents.father)
    mother = property(lambda self: self.parents.mother)


class Parents(object):
    children = relations.Many(backref=".Person:parents")
    father = relations.One(backref=".Person:father_of")
    mother = relations.One(backref=".Person:mother_of")
"""

from __future__ import absolute_import
from copy import copy
import operator

from utils.prettyrepr import prettify_class


def setattr_decorator(attr, decorator_name=None):
    """This creates a decorator function that should be used as an instance method. What the
    created decorator does is store the decorated function in on a
    of RelationSide. The decorator creates a (shallow) copy of the relation side object and
    sets a particular attribute (usually a simplex operator function) on the clone. The idea is
    much like the builtin property(), allowing subclasses to change the way relation sides
    work without affecting the instances of the base class."""
    def decorator(obj, fnc):
        clone = copy(obj)
        setattr(clone, attr, fnc)
        return clone

    if decorator_name is None:
        decorator_name = "set_%s" % (attr,)
    decorator.__name__ = decorator_name
    return decorator


class RelationSide(object):
    """Base class for One and Many, the two types of relation sides."""
    def __init__(self, complement):
        self.complement = complement  # str: attr name to which the other relation side is bound

    def simplex_accepts(self, obj, other):
        pass

    def duplex_accepts(self, obj, other):
        """Before setting a One property or adding an element to a Many property, this method is
        used to confirm if the operation is accepted by both sides of the relation. The simplex
        acceptance methods should raise an exception if something is wrong with the relation."""
        self.simplex_accepts(obj, other)
        complement = getattr(type(other), self.complement)
        complement.simplex_accepts(other, obj)

    accepts = setattr_decorator("simplex_accepts", "accepts")


class One(RelationSide):
    """A One relation side can associate one object at a time. When a new object is associated, any
    former relation is undone on both sides automatically."""
    def __init__(self, fget=None, fset=None, fdel=None, complement=None):
        RelationSide.__init__(self, complement)
        self.fget = fget  # simplex get function
        self.fset = fset  # simplex set function
        self.fdel = fdel  # simplex del function

    getter = __call__ = setattr_decorator("fget", "getter")
    setter = setattr_decorator("fset", "setter")
    deleter = setattr_decorator("fdel", "deleter")

    def __get__(self, obj, owner):
        return self if obj is None else self.fget(obj)

    def simplex_set(self, obj, new_value):
        self.fset(obj, new_value)

    def duplex_set(self, obj, new_value):
        old_value = self.fget(obj)
        if new_value is old_value:
            return
        if new_value is not None:
            self.duplex_accepts(obj, new_value)
        if old_value is not None:
            self.duplex_delete(obj)
        if new_value is not None:
            complement = getattr(type(new_value), self.complement)
            if isinstance(complement, One):
                complement.duplex_delete(new_value)
                complement.simplex_set(new_value, obj)
            else:
                complement.simplex_add(new_value, obj)
            self.simplex_set(obj, new_value)

    __set__ = duplex_set

    def simplex_delete(self, obj):
        if self.fdel is not None:
            self.fdel(obj)
        else:
            self.fset(obj, None)

    def duplex_delete(self, obj):
        value = self.fget(obj)
        if value is not None:
            complement = getattr(type(value), self.complement)
            if isinstance(complement, One):
                complement.simplex_delete(value)
            else:
                complement.simplex_remove(value, obj)
            self.simplex_delete(obj)

    __delete__ = duplex_delete


def default_fadd(container, elem):
    container.add(elem)


def default_fremove(container, elem):
    container.remove(elem)


default_flen = len
default_fiter = iter
default_fcontains = operator.contains


class Many(RelationSide):
    """A Many side can hold any number of objects. Accessing this side as a property of an object
    will yield a BoundMany object, which provides a traditional container interface (__len__,
    __iter__, __contains__, add, remove, discard, update, difference_update, and clear).
    The add() and remove() methods of the BoundMany object are duplex, using the duplex add and
    remove methods of this Many object."""
    def __init__(self, fget=None, fadd=default_fadd, fremove=default_fremove, flen=default_flen,
                 fiter=default_fiter, fcontains=default_fcontains, complement=None):
        RelationSide.__init__(self, complement)
        self.fget = fget
        self.fadd = fadd
        self.fremove = fremove
        self.flen = flen
        self.fiter = fiter
        self.fcontains = fcontains

    getter = __call__ = setattr_decorator("fget", "getter")
    adder = setattr_decorator("simplex_add", "adder")
    remover = setattr_decorator("simplex_remove", "remover")
    len = setattr_decorator("simplex_len", "len")
    iter = setattr_decorator("simplex_iter", "iter")
    contains = setattr_decorator("simplex_contains", "contains")

    def __get__(self, obj, owner):
        return self if obj is None else BoundMany(self, obj)

    def simplex_add(self, obj, elem):
        self.fadd(self.fget(obj), elem)

    def duplex_add(self, obj, elem):
        self.duplex_accepts(obj, elem)
        complement = getattr(type(elem), self.complement)
        if isinstance(complement, Many):
            complement.simplex_add(elem, obj)
        else:
            complement.duplex_delete(elem)
            complement.simplex_set(elem, obj)
        self.simplex_add(obj, elem)

    def simplex_remove(self, obj, elem):
        self.fremove(self.fget(obj), elem)

    def duplex_remove(self, obj, elem):
        complement = getattr(type(elem), self.complement)
        if isinstance(complement, Many):
            complement.simplex_remove(elem, obj)
        else:
            complement.simplex_delete(elem)
        self.simplex_remove(obj, elem)

    def simplex_len(self, obj):
        return self.flen(self.fget(obj))

    def simplex_iter(self, obj):
        return self.fiter(self.fget(obj))

    def simplex_contains(self, obj, elem):
        return self.fcontains(self.fget(obj), elem)


@prettify_class
class BoundMany(object):
    """A Many relation side object bound to a particular object. This serves merely as a proxy to
    the methods on the Many object, bound to an associated object. """
    __slots__ = ("side", "obj")

    def __init__(self, side, obj):
        self.side = side  # Many object
        self.obj = obj    # the object to which this relation side is associated

    def __info__(self):
        return ", ".join(repr(elem) for elem in self)

    def __len__(self):
        return self.side.simplex_len(self.obj)

    def __iter__(self):
        return self.side.simplex_iter(self.obj)

    def __contains__(self, elem):
        return self.side.simplex_contains(self.obj, elem)

    def add(self, *elems):
        self.update(elems, force=True)

    def remove(self, *elems):
        self.difference_update(elems, force=True)

    def discard(self, *elems):
        self.difference_update(elems, force=False)

    def update(self, elems, force=False):
        duplex_add = self.side.duplex_add
        obj = self.obj
        for elem in elems:
            if force or elem not in self:
                duplex_add(obj, elem)

    def difference_update(self, elems, force=False):
        duplex_remove = self.side.duplex_remove
        obj = self.obj
        for elem in elems:
            if force or elem in self:
                duplex_remove(obj, elem)

    def clear(self):
        while len(self) > 0:
            self.remove(iter(self).next())


def _demo():
    """A fairly simple illustrative demo of a one-to-many relation between Bars and Foos."""
    class Foo(object):
        _bar = None

        def __init__(self, x):
            self.x = x

        def __repr__(self):
            b = None if self._bar is None else self._bar.x
            return "%s#%s(b=%s)" % (type(self).__name__, self.x, b)

        @One(complement="f")
        def b(self):
            print "%s getting b -> %s" % (self, self._bar)
            return self._bar

        @b.setter
        def b(self, bar):
            print "%s setting b to %s" % (self, bar)
            self._bar = bar

        @b.deleter
        def b(self):
            print "%s deleting b %s" % (self, self._bar)
            del self._bar

    class Bar(object):
        def __init__(self, x):
            self.x = x
            self._foo = []

        def __repr__(self):
            fs = ", ".join(str(f.x) for f in self._foo)
            return "%s#%s(f=[%s])" % (type(self).__name__, self.x, fs)

        @Many(complement="b")
        def f(self):
            return self._foo

        @f.adder
        def f(self, foo):
            print "%s adding f %s" % (self, foo)
            self._foo.append(foo)

        @f.remover
        def f(self, foo):
            print "%s removing f %s" % (self, foo)
            self._foo.remove(foo)

    f = [Foo(x) for x in xrange(10)]
    b = [Bar(x) for x in xrange(2)]
    b[0].f.update(f)
    f[5].b = b[1]
    return f, b

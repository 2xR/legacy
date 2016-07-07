"""REJECTED on account of being too complicated a solution which can be replaced with lambdas of
similar length in the most frequent cases.

Simple module for function-like getters, setters, and deleters of arbitrarily-nested items and/or
attributes.
Examples:

    fget = getter.foo[0].bar[-3]
    # is equivalent to
    fget = lambda o: o.foo[0].bar[-3]
    print fget(obj)

    fset = setter[0].abc[3][3]
    # is equivalent to
    fset = lambda o, v: setitem(o[0].abc[3], 3, v)
    fset(obj, val)

    fdel = deleter.x.y.z
    # is equivalent to
    fdel = lambda o: delattr(o.x.y, "z")
    # def fdel(o):
    #     del o.x.y.z
    fdel(obj)

These function-like objects can be useful for functional-style programming, e.g. map.
"""
__all__ = ["getter", "setter", "deleter"]


class Operator(object):
    __slots__ = ("_path",)

    def __init__(self, parent):
        if parent is None:
            self._path = [self]
        else:
            self._path = parent._path + [self]

    def __repr__(self):
        return "".join(op._info() for op in self._path)

    def __getitem__(self, key):
        return ItemOperator(self, key)

    def __getattr__(self, attr):
        return AttrOperator(self, attr)

    def __call__(self, obj, *args):
        path = self._path
        for i in xrange(1, len(path) - 1):
            obj = path[i]._get(obj)
        method = getattr(self, path[0]._method)  # method to call determined by root operator
        return method(obj, *args)

    def _info(self):
        raise NotImplementedError()

    def _get(self, obj):
        raise NotImplementedError()

    def _set(self, obj, val):
        raise NotImplementedError()

    def _del(self, obj):
        raise NotImplementedError()


class ItemOperator(Operator):
    __slots__ = ("_key",)

    def __init__(self, parent, key):
        Operator.__init__(self, parent)
        self._key = key

    def _info(self):
        return "[{!r}]".format(self._key)

    def _get(self, obj):
        return obj[self._key]

    def _set(self, obj, val):
        obj[self._key] = val

    def _del(self, obj):
        del obj[self._key]


class AttrOperator(Operator):
    __slots__ = ("_attr",)

    def __init__(self, parent, attr):
        Operator.__init__(self, parent)
        self._attr = attr

    def _info(self):
        return ".{!s}".format(self._attr)

    def _get(self, obj):
        return getattr(obj, self._attr)

    def _set(self, obj, val):
        setattr(obj, self._attr, val)

    def _del(self, obj):
        delattr(obj, self._attr)


class OperatorRoot(Operator):
    __slots__ = ("_name", "_method")

    def __init__(self, name, method):
        Operator.__init__(self, None)
        self._name = name
        self._method = method

    def _info(self):
        return self._name


getter = OperatorRoot(name="getter", method="_get")
setter = OperatorRoot(name="setter", method="_set")
deleter = OperatorRoot(name="deleter", method="_del")


def example():
    from utils.misc import UNDEF

    class Foo(object):
        def __repr__(self):
            return repr(self.__dict__)

        def __getitem__(self, i):
            v = self.__dict__.get(i, UNDEF)
            print "[{!r}] -> {!r}".format(i, v)
            return v if v is not UNDEF else self

        def __setitem__(self, i, v):
            print "[{!r}] <- {!r}".format(i, v)
            self.__dict__[i] = v

        def __delitem__(self, i):
            v = self.__dict__.pop(i, UNDEF)
            print "del [{!r}] >> {!r}".format(i, v)

        def __getattr__(self, a):
            v = self.__dict__.get(a, UNDEF)
            print ".{!s} -> {!r}".format(a, v)
            return v if v is not UNDEF else self

        def __setattr__(self, a, v):
            print ".{!s} <- {!r}".format(a, v)
            self.__dict__[a] = v

        def __delattr__(self, a):
            v = self.__dict__.pop(a, UNDEF)
            print "del .{!s} >> {!r}".format(a, v)

    foo = Foo()
    fget = getter.a[0].b[1].c[2]
    fset = setter.a[0].b[1].c[2]
    fdel = deleter.a[0].b[1].c[2]
    print "****", foo
    for fnc, args in [(fset, ["hello"]),
                      (fget, []),
                      (fset, ["world"]),
                      (fdel, []),
                      (fget, [])]:
        print ">>>>", fnc, args
        fnc(foo, *args)
        print "****", foo, "\n"

from types import MethodType
from functools import wraps
from collections import Iterable

from utils.multidict import merge
from utils.prettyrepr import prettify_class


def curry(func, *args, **keywords):
    """This function does the same as functools.partial, but this actually creates a function
    object. This has the advantage of being treated properly by a class, since a bound method is
    not created by classes for 'partial' objects. This probably has worse performance though.
    The returned function's positional and keyword arguments can be accessed and modified through
    the 'args' and 'keywords' attributes, just like partial objects."""
    @wraps(func)
    def curried_func(*extra_args, **extra_keywords):
        args = curried_func.args
        keywords = curried_func.keywords
        final_args = (args if len(extra_args) == 0 else
                      extra_args if len(args) == 0 else
                      args + extra_args)
        final_keywords = (keywords if len(extra_keywords) == 0 else
                          extra_keywords if len(keywords) == 0 else
                          merge((keywords, extra_keywords)))
        return curried_func.func(*final_args, **final_keywords)
    curried_func.func = func
    curried_func.args = args
    curried_func.keywords = keywords
    return curried_func


@prettify_class
class MultiCall(list):
    """Call a list of functions (with the same arguments) as if it were a single function call.
    MultiCall objects have a "return mode" which determines what is returned when the MultiCall
    object is called as a regular callable (i.e. through __call__).
    There are currently four return modes (default=DISCARD_RESULTS), available as constants in the
    MultiCall class:
        - DISCARD_RESULTS - all functions are called immediately, but the multicall always returns
            None.
        - FIRST_RESULT - all functions are called immediately, but only the result of the first
            function is returned. Any results from the remaining functions are discarded.
        - ITER_RESULTS - functions are called lazily, using a generator. The generator yields the
            return values of all functions.
        - LIST_RESULTS - immediately consumes the generator produced by iter_results() and saves
            all the results into a python list, which is then returned by the multicall object.

    Note that the return mode only controls what is returned by __call__(). Any of the modes can be
    explicitly used by calling the appropriate method on the multicall object.
    """
    __slots__ = ("__weakref__", "return_mode")
    DISCARD_RESULTS = NO_RESULT = 0
    FIRST_RESULT = 1
    ITER_RESULTS = 2
    LIST_RESULTS = ALL_RESULTS = 3
    RETURN_MODE_NAMES = ("discard", "first", "iter", "list")

    def __init__(self, iterable=None, return_mode=DISCARD_RESULTS):
        if iterable is None:
            list.__init__(self)
        elif isinstance(iterable, Iterable):
            list.__init__(self, iterable)
        else:
            list.__init__(self)
            self.append(iterable)
        self.return_mode = return_mode

    def __info__(self):
        return "<%s> return_mode=%s" % (", ".join(f.__name__ for f in self),
                                        type(self).RETURN_MODE_NAMES[self.return_mode])

    def discard_results(self, *args, **kwargs):
        for fnc in self:
            fnc(*args, **kwargs)

    def first_result(self, *args, **kwargs):
        if len(self) == 0:
            return None
        else:
            result = self[0](*args, **kwargs)
            for i in xrange(1, len(self)):
                self[i](*args, **kwargs)
            return result

    def iter_results(self, *args, **kwargs):
        for fnc in self:
            yield fnc(*args, **kwargs)

    def list_results(self, *args, **kwargs):
        return list(self.iter_results(*args, **kwargs))

    __callmap__ = (discard_results, first_result, iter_results, list_results)

    def __call__(self, *args, **kwargs):
        return type(self).__callmap__[self.return_mode](self, *args, **kwargs)

    @property
    def __name__(self):
        return "%s<%s>" % (type(self).__name__, ", ".join(f.__name__ for f in self))


class CoopCall(object):
    """A CoopCall object is similar to a super object, but it gets a list of classes as a
    parameter, and executes all methods at once (actually a MultiCall object is returned, which
    may execute one at a time with iter_results()).

    The CoopCall class is similar in role to python's controversial builtin 'super()', but it does
    what it promises to do, as opposed to super which seems like black magic to those that don't
    really understand the mechanism (hell, I do understand it and I still don't want to use it
    because it is very counter-intuitive, e.g. in cases of complex multiple inheritance graphs...)

    In CoopCall, a list of classes from where methods will be executed is specified, so there is
    no doubt about what gets called and what order is used."""
    def __init__(self, classes=None, target=None):
        if classes is None and target is not None:
            classes = reversed(type(target).mro())
        self.classes = list(classes)
        self.target = target

    def __getattr__(self, name):
        methods = MultiCall()
        for cls in self.classes:
            method = cls.__dict__.get(name, None)
            if method is not None:
                if self.target is not None:
                    method = MethodType(method, self.target, cls)
                methods.append(method)
        return methods


def _test():
    class A(object):
        def foo(self):
            print "bar", self

    class B(A):
        def foo(self):
            print "baz", self

    class C(A):
        def foo(self):
            print "xaz", self

    class D(B, C):
        def foo(self):
            print "dix", self

    d = D()
    f = CoopCall(classes=D.mro(), target=d)  # bound to instance
    f.foo()

    g = CoopCall(classes=D.mro(), target=D)  # bound to class
    g.foo()

    h = CoopCall(classes=D.mro())  # unbound
    h.foo("OMG!!")

from __future__ import absolute_import
import sys
import threading
import random
import operator
from functools import partial, wraps
from itertools import izip_longest
from collections import Iterable, deque, defaultdict
from contextlib import contextmanager

__all__ = ["IDGenerator", "Singleton", "Undefined", "Undef", "MAXINT", "MAXFLOAT", "Inf", "NaN",
           "dummy_fnc", "identity_fnc", "ensure_type", "mismatching_type", "ensure_subclass",
           "not_a_subclass", "ignored", "reversed_args", "separate_thread", "recursion_limit",
           "callable_name", "is_sorted", "sorted_indices", "biased_choice",
           "unzip", "argmax", "argmin", "max_elems", "min_elems", "group_by", "dict_diff",
           "dict_extract", "first", "getitem", "mutation_safe_iter_set", "multikey_lookup",
           "sequence_differences", "union", "chain", "consume", "flat_iter", "slice_iter",
           "rotating_iter", "compose"]


# --------------------------------------------------------------------------------------------------
# Small utility classes that don't justify a separate file and don't fit in a larger group
class IDGenerator(defaultdict):
    """This little class can be useful to quickly generate identifiers for objects."""
    __slots__ = ()

    def __init__(self):
        defaultdict.__init__(self, int)

    def generate(self, obj):
        cls = type(obj)
        n = self[cls]
        identifier = "{}#{}".format(cls.__name__, n)
        self[cls] = n + 1
        return identifier

    __call__ = generate


# --------------------------------------------------------------------------------------------------
# Miscellaneous functions
def reversed_args(func, name=None, doc=None):
    """Creates a function that wraps 'func', passing it the arguments it received in reverse
    order. Note that only positional arguments are reversed. Any keyword arguments are passed
    without modifications to the original function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*reversed(args), **kwargs)
    if name is not None:
        wrapper.__name__ = name
    if doc is not None:
        wrapper.__doc__ = doc
    return wrapper


def separate_thread(func):
    """Function decorator that wraps the decorated function making it run in a separate thread.
    However, the wrapper returns immediately without any return value from the original function,
    so this is only appropriate for functions with side effects and whose return value(s) may be
    safely discarded.

    Usage example:
        import threading
        import time

        @separate_thread
        def foo(x):
            print "before sleep():", threading.active_count(), "active threads"
            time.sleep(x)
            print "after sleep():", threading.active_count(), "active threads"
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=partial(func, *args, **kwargs))
        thread.start()
        return thread
    return wrapper


@contextmanager
def recursion_limit(n):
    """Context manager that temporarily sets Python's recursion limit to 'n', and restores the
    previous recursion limit when the context is exited."""
    m = sys.getrecursionlimit()
    sys.setrecursionlimit(n)
    yield
    sys.setrecursionlimit(m)


def callable_name(obj):
    """Return the name of a callable object (a function, method, functools.partial). If the object
    does not have a __name__ attribute and is not a partial object, its repr() is returned."""
    try:
        return obj.__name__
    except AttributeError:
        if isinstance(obj, partial):
            return callable_name(obj.func)
        else:
            return repr(obj)






def mutation_safe_iter_set(S):
    """An iterator that allows traversing a set while making it safe to add or remove elements
    during iteration. New elements will eventually appear (no order is guaranteed) in the iterator,
    and removed elements will be skipped (unless they have already been iterated over, of course).
    Note that this is not very efficient since it makes a copy of the whole set and a bunch of set
    operations at each iteration, to determine if elements were added to or removed from the
    original set."""
    ensure_type(S, set)
    R = set(S)  # remaining elements
    while len(R) > 0:
        T = set(S)  # copy of S
        yield R.pop()
        N = S - T  # new elements in S
        D = T - S  # elements deleted from S
        R.difference_update(D)
        R.update(N)

from __future__ import absolute_import
import sys
import threading
import random
import operator
from functools import partial, wraps
from itertools import izip_longest
from collections import Iterable, deque, defaultdict
from contextlib import contextmanager

__all__ = ["IDGenerator", "Singleton", "Undefined", "UNDEF", "MAXINT", "MAXFLOAT", "INF", "NAN",
           "dummy_fnc", "identity_fnc", "check_type", "mismatching_type", "check_subclass",
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


class Singleton(object):
    """Basic singleton class. Subclasses must implement the __singleton__() method as an instance
    initializer instead of __init__(), because __init__() is called implicitly by Python multiple
    times (one time per constructor call, since the __new__() method returns an instance of the
    class)."""
    def __new__(cls, *args, **kwargs):
        if "__instance__" not in cls.__dict__:
            cls.__instance__ = object.__new__(cls, *args, **kwargs)
            cls.__instance__.__singleton__(*args, **kwargs)
        return cls.__instance__

    def __singleton__(self, *args, **kwargs):
        pass


class Undefined(Singleton):
    """Utility class for undefined arguments when None may be a valid argument value."""
    def __repr__(self):
        return "UNDEF"

# --------------------------------------------------------------------------------------------------
# (very!) Useful constants
UNDEF = Undefined()
MAXINT = sys.maxint
MAXFLOAT = sys.float_info.max
INF = float("inf")
NAN = float("nan")


# --------------------------------------------------------------------------------------------------
# Miscellaneous functions
def dummy_fnc_no_args():
    pass


def dummy_fnc_any_args(*args, **kwargs):
    pass

dummy_fnc = dummy_fnc_any_args
dummy_fnc.no_args = dummy_fnc_no_args
dummy_fnc.any_args = dummy_fnc_any_args
del dummy_fnc_no_args
del dummy_fnc_any_args


def identity_fnc(x):
    """Plain old identity function. Returns its argument, unmodified. :)"""
    return x


def check_type(obj, cls, none_allowed=False):
    """A simple type-checking function that raises a TypeError if 'obj' is not as instance of
    'cls'. The second argument, 'cls', may be a type or a tuple of classes, like the argument to
    isinstance(). If 'none_allowed' is true, no error is raised if 'obj' is None."""
    if not isinstance(obj, cls) and not (none_allowed and obj is None):
        raise mismatching_type(obj, cls, none_allowed)
    return True


def mismatching_type(obj, cls, none_allowed=False):
    """Creates a TypeError instance with a helpful description of the error."""
    if isinstance(cls, tuple):
        cls_name = "one of {" + ", ".join(c.__name__ for c in cls) + "}"
    else:
        cls_name = cls.__name__
    if none_allowed:
        cls_name += " (or None)"
    return TypeError("{} expected, got {} instead".format(cls_name, type(obj).__name__))


def check_subclass(cls, super_cls):
    """Similar to check_type(), but for checking if a class is a subclass of another."""
    if not issubclass(cls, super_cls):
        raise not_a_subclass(cls, super_cls)
    return True


def not_a_subclass(cls, super_cls):
    """Creates a TypeError instance with a helpful description of the error."""
    if isinstance(super_cls, tuple):
        super_cls_name = "one of {" + ", ".join(c.__name__ for c in super_cls) + "}"
    else:
        super_cls_name = super_cls.__name__
    return TypeError("expected subclass of {}, got {} instead"
                     .format(super_cls_name, cls.__name__))


@contextmanager
def ignored(*exceptions):
    """This context manager simply ignores any of the given exceptions occurring within its
    scope."""
    try:
        yield
    except exceptions:
        pass


def reversed_args(func, name=None, doc=None):
    """Creates a function that wraps 'func', passing it the arguments it received in reverse
    order. Note that only positional arguments are reversed. Any keyword arguments are passed
    without modifications to the original function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*reversed(args), **kwargs)
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


def is_sorted(sequence, key=None, reverse=False):
    """Checks whether a sequence is sorted, that is, for every pair of consecutive elements (i,j),
    key(i) <= key(j) is true. If key is not given, the elements in the sequence themselves are
    compared."""
    iterator = iter(sequence)
    try:
        item = iterator.next()
    except StopIteration:
        return True
    prev_key = key(item) if key is not None else item
    ordered = operator.ge if reverse else operator.le
    for item in iterator:
        curr_key = key(item) if key is not None else item
        if not ordered(prev_key, curr_key):
            return False
        prev_key = curr_key
    return True


def sorted_indices(sequence, key=None, reverse=False):
    """This function works like the builtin sorted(), but instead of returning a sorted list of
    items, it returns a list of indices in the original list such that traversing the list using
    those indices will yield the same sorted list as sorted() returns.
        words = "this is a very long sentence that will serve as an example".split()
        sorted_words0 = sorted(words)
        sorted_words1 = [words[i] for i in sorted_indices(words)]
        # or sorted_words1 = map(words.__getitem__, sorted_indices(words))
        assert sorted_items0 == sorted_items1
    """
    _key = sequence.__getitem__ if key is None else lambda i: key(sequence[i])
    indices = range(len(sequence))
    indices.sort(key=_key, reverse=reverse)
    return indices


def biased_choice(biases, rng=random):
    """Randomly pick an integer index using different probabilities for selecting each index. The
    list 'biases' should contain the bias (or weight) of each index in the random draw. Biases
    should be non-negative real numbers of any magnitude. The probability of each index is the
    quotient between its bias and the sum of all biases."""
    assert all(bias >= 0.0 for bias in biases)
    X = rng.uniform(0.0, sum(biases))
    Y = 0.0
    for index, bias in enumerate(biases):
        Y += bias
        if Y >= X:
            return index
    raise Exception("They came from behind!!! We're not supposed to be here... really...")


def unzip(iterable, fillvalue=None):
    """Inverse of the built-in zip() function. Returns a list of lists, all with size equal to the
    argument iterable's size. Any missing values are replaced by 'fillvalue'."""
    lists = []
    count = 0
    for values in iterable:
        # create new lists if the current tuple has more values than we currently have lists
        if len(lists) < len(values):
            lists.extend(([fillvalue] * count) for _ in xrange(len(values) - len(lists)))
        # append each value to the appropriate list
        for i in xrange(len(values)):
            lists[i].append(values[i])
        # not enough values, append fillvalue to the remaining lists
        if len(values) < len(lists):
            for i in xrange(len(values), len(lists)):
                lists[i].append(fillvalue)
        count += 1
    return lists


def argmax(iterable, key=None, gt=operator.gt, eq=operator.eq):
    """Find the indices of items in 'iterable' corresponding to the maximum values w.r.t. 'key'.
    'gt' should be a boolean function returning True if the current key is greater than the current
    highest key (the default 'gt' function is the > operator).
    'eq' is another function argument that also takes two keys and should return True if they are
    identical (the default 'eq' function is the == operator).
    Returns a list of indices."""
    iterator = iter(iterable)
    try:
        elem = iterator.next()
    except StopIteration:
        raise ValueError("argument iterable must be non-empty")
    curr_index = 0
    max_indices = [curr_index]
    max_key = elem if key is None else key(elem)
    for elem in iterator:
        curr_index += 1
        curr_key = elem if key is None else key(elem)
        if gt(curr_key, max_key):
            max_indices = [curr_index]
            max_key = curr_key
        elif eq(curr_key, max_key):
            max_indices.append(curr_index)
    return max_indices


def argmin(iterable, key=None, lt=operator.lt, eq=operator.eq):
    """Like argmax(), but returns the indices corresponding to the minimum values w.r.t 'key'.
    The default 'lt' function is the < operator. Returns a list of indices."""
    return argmax(iterable, key, lt, eq)


def max_elems(iterable, key=None, gt=operator.gt, eq=operator.eq):
    """Find the elements in 'iterable' corresponding to the maximum values w.r.t. 'key'. 'gt'
    should be a boolean function returning True if the current key is greater than the current
    highest key (the default 'gt' function is the > operator).
    'eq' is another function argument that also takes two keys and should return True if they are
    identical (the default 'eq' function is the == operator).
    Returns a list of elements from 'iterable'."""
    iterator = iter(iterable)
    try:
        elem = iterator.next()
    except StopIteration:
        raise ValueError("argument iterable must be non-empty")
    max_elems = [elem]
    max_key = elem if key is None else key(elem)
    for elem in iterator:
        curr_key = elem if key is None else key(elem)
        if gt(curr_key, max_key):
            max_elems = [elem]
            max_key = curr_key
        elif eq(curr_key, max_key):
            max_elems.append(elem)
    return max_elems


def min_elems(iterable, key=None, lt=operator.lt, eq=operator.eq):
    """Same as max_elems(), but for finding the minimum elements."""
    return max_elems(iterable, key, lt, eq)


def group_by(iterable, key):
    """Given an 'iterable' and a 'key' function, create and return a dictionary mapping keys to
    lists of elements that have the same key."""
    groups = {}
    for elem in iterable:
        k = key(elem)
        try:
            groups[k].append(elem)
        except KeyError:
            groups[k] = [elem]
    return groups


def dict_diff(a, b):
    """Compute the difference between dictionaries a and b, as a - b. The resulting dictionary
    includes keys from a which are not present in b, plus all keys in a whose value is different
    in b."""
    return {k: v for (k, v) in a.iteritems() if k not in b or v != b[k]}


def dict_extract(d, keys, skip_missing_keys=False):
    """Create a dictionary by only extracting the keys in 'keys' from 'd'. Raises a KeyError if a
    key is not present in 'd' and 'skip_missing_keys' is false, otherwise silently skips the key.
    """
    if skip_missing_keys:
        return {k: d[k] for k in keys if k in d}
    else:
        return {k: d[k] for k in keys}


def first(iterable, default=UNDEF):
    """Return the first element of the argument 'iterable'. This is a utility function to avoid the
    not-so-uncommon-as-you-might-like idiom on sets and dictionaries:
        d = {"a": 1, "b": 2, "c": 3}
        some_key = iter(d).next()

    This function works very similarly to the builtin next() function, allowing a default value to
    be returned when 'iterable' is empty."""
    iterator = iter(iterable)
    try:
        return iterator.next()
    except StopIteration as exception:
        if default is UNDEF:
            raise exception
        return default


def getitem(sequence, index=0, default=UNDEF):
    """Retrieve the 'index'-th of 'sequence', which can be an actual sequence type or an iterator.
    Note however that if 'sequence' is an iterator, this ends up linearly scanning through all the
    items until reaching the desired index."""
    try:
        return sequence[index]
    except IndexError:
        if default is UNDEF:
            raise
        return default
    except TypeError:
        item = None
        iterator = iter(sequence)
        for _ in xrange(index+1):
            try:
                item = iterator.next()
            except StopIteration:
                if default is UNDEF:
                    raise
                return default
        return item


def mutation_safe_iter_set(S):
    """An iterator that allows traversing a set while making it safe to add or remove elements
    during iteration. New elements will eventually appear (no order is guaranteed) in the iterator,
    and removed elements will be skipped (unless they have already been iterated over, of course).
    Note that this is not very efficient since it makes a copy of the whole set and a bunch of set
    operations at each iteration, to determine if elements were added to or removed from the
    original set."""
    check_type(S, set)
    R = set(S)  # remaining elements
    while len(R) > 0:
        T = set(S)  # copy of S
        yield R.pop()
        N = S - T  # new elements in S
        D = T - S  # elements deleted from S
        R.difference_update(D)
        R.update(N)


def multikey_lookup(D, *K):
    """Lookup all keys 'K' in 'D', in order. Returns the value associated with the first key that
    is found in 'D'. If none of the keys are found, KeyError is raised."""
    for k in K:
        try:
            return D[k]
        except KeyError:
            pass
    raise KeyError("unable to find any key {0} in {1}".format(K, D))


def sequence_differences(*sequences, **kwargs):
    """Given one or more sequences, find the differences between them. Returns a list of indices
    together with the differing elements of each argument sequence."""
    key = kwargs.get("key", identity_fnc)
    fillvalue = kwargs.get("fillvalue", UNDEF)
    diff = []
    for i, elems in enumerate(izip_longest(*sequences, fillvalue=fillvalue)):
        key_x = key(elems[0])
        if any(key(y) != key_x for y in elems[1:]):
            diff.append((i, elems))
    return diff


class union(object):
    """Represents a union of containers. It is useful merely to test for membership in a list of
    containers at once."""
    __slots__ = ("containers",)

    def __init__(self, *containers):
        self.containers = list(containers)

    def __repr__(self):
        return "<{}({}) @{:08x}>".format(type(self).__name__, self.containers, id(self))

    def __contains__(self, elem):
        return any(elem in container for container in self.containers)


class chain(object):
    """An iterable object which emulates a sequence consisting of the concatenation of the elements
    in the argument iterables. This behaves almost exactly like 'chain()' in itertools, except that
    this object can be iterated multiple times and not just once.
    Note that the *only* thing you can actually do with a chain object is iteration."""
    __slots__ = ("iterables",)

    def __init__(self, *iterables):
        self.iterables = iterables

    def __iter__(self):
        for iterable in self.iterables:
            for elem in iterable:
                yield elem


def consume(iterator, n=INF):
    """Consume the next 'n' elements in 'iterator'. Returns a 2-tuple with the iterator and the
    number of elements that were consumed."""
    iterator = iter(iterator)
    i = 0
    while i < n:
        try:
            iterator.next()
        except StopIteration:
            break
        i += 1
    return iterator, i


def consume_until(iterable, predicate=bool):
    iterator = iter(iterable)
    for x in iterator:
        if predicate(x):
            return iterator, x
    raise StopIteration("unable to find positive value")


def flat_iter(iterable, flatten=Iterable, depth=INF):
    """Returns a flat iterator over the items of the argument 'iterable'. Only elements of iterable
    which are of the type(s) specified by 'flatten' (may be a single type or a tuple of types) are
    flattened. Note that these elements should at least be iterable (iter() is called on them)."""
    stack = [iter(iterable)]
    while len(stack) > 0:
        it = stack[-1]
        try:
            elem = it.next()
        except StopIteration:
            stack.pop()
        else:
            if (((len(stack) <= depth and
                  isinstance(elem, flatten) and
                  not (isinstance(elem, basestring) and len(elem) == 1)
                  ))):
                stack.append(iter(elem))
            else:
                yield elem


def slice_iter(iterable, start=0, stop=None, step=None):
    """Iterate over a slice of 'iterable' defined by 'start', 'stop', and 'step'. This avoids the
    creation of temporary lists, as in the slicing of a built-in list."""
    start, stop, step = slice(start, stop, step).indices(len(iterable))
    iterator = iter(iterable)
    if start > 0:
        consume(iterator, start)
    pos = start
    skip = step - 1
    while pos < stop:
        yield iterator.next()
        pos += 1
        if skip > 0:
            consume(iterator, skip)
            pos += skip


class slice_iterator(object):
    """Similar to slice_iter, but this object can be iterated multiple times. Also, if the
    underlying iterable changes size, new iterations over this object will adjust appropriately.
    """
    def __init__(self, iterable=None, start=0, stop=None, step=None):
        self.iterable = iterable
        self.start = start
        self.stop = stop
        self.step = step

    def __getitem__(self, i):
        if isinstance(i, slice):
            return slice_iterator(self.iterable, i.start, i.stop, i.step)
        elif self.iterable is None and isinstance(i, Iterable):
            return slice_iterator(i, self.start, self.stop, self.step)
        else:
            return self.iterable[i]

    def __iter__(self):
        return slice_iter(self.iterable, self.start, self.stop, self.step)


def rotating_iter(iterable, size=2, step=1):
    """A rotating iterator. Yields tuples with 'size' contiguous elements from 'iterable', then
    moves forward 'step' elements, rotating out the older elements and replacing them with more
    recent elements. With default arguments, this iterates over consecutive pairs of elements in
    the argument 'iterable'.
    Note that if 'size' and 'step' are provided, the last few elements of 'iterable' may not be
    returned if its size is not equal to 'size + k * step', where 'k' is a non-negative integer.
    """
    d = deque(maxlen=size)
    it = iter(iterable)
    for _ in xrange(size):
        try:
            x = it.next()
        except StopIteration:
            return
        else:
            d.append(x)
    while True:
        yield tuple(d)
        for _ in xrange(step):
            try:
                x = it.next()
            except StopIteration:
                return
            else:
                d.append(x)


def compose(*funcs):
    """Creates a composite function, which applies each argument function to the result of the next
    function.  The order of application is the same as in mathematics, i.e.
        compose(f, g)(3) is equivalent to f(g(3))
    """
    if len(funcs) < 2:
        raise ValueError("at least two functions are required")
    funcs = list(funcs)
    funcs.reverse()

    def compose_func(*args, **kwargs):
        funcs_iter = iter(funcs)
        result = funcs_iter.next()(*args, **kwargs)
        for f in funcs_iter:
            result = f(result)
        return result

    compose_func.funcs = funcs
    return compose_func

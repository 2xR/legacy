from __future__ import absolute_import
import rr
from collections import Mapping, Iterable, deque
from itertools import islice
import operator


def is_sorted(sequence, key=None, reverse=False):
    """Checks whether a sequence is sorted, that is, for every pair of consecutive elements
    (i,j), key(i) <= key(j) is true. If key is not given, the elements in the sequence themselves
    are compared. """
    iterator = iter(sequence)
    try:
        item = next(iterator)
    except StopIteration:
        return True
    prev_key = item if key is None else key(item)
    ordered = operator.ge if reverse else operator.le
    for item in iterator:
        curr_key = item if key is None else key(item)
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
        assert sorted_words0 == sorted_words1
    """
    _key = sequence.__getitem__ if key is None else lambda i: key(sequence[i])
    indices = xrange(len(sequence))
    return sorted(indices, key=_key, reverse=reverse)


def unzip(iterable, fillvalue=None):
    """Inverse of the built-in zip() function. Returns a list of lists, all with size equal to
    the argument iterable's size. Any missing values are replaced by 'fillvalue'. """
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


def max_pairs(iterable, key=None, gt=operator.gt, eq=operator.eq):
    """Find the pairs (index, elem) in 'iterable' corresponding to the maximum elements with
    respect to 'key'. If 'iterable' is a mapping object, a list of (key, value) pairs is returned
    instead.

    :param iterable: the iterable on which we're operating. Can also be a mapping, such as a
        dictionary, in which case pairs (key, value) are returned.
    :param key: a key function as in the built-in sorted().
    :param gt: a boolean function returning True if the current key is greater than the current
        highest key (the default 'gt' function is the > operator).
    :param eq: another function argument that also takes two keys and should return True if they
        are identical (the default 'eq' function is the == operator).
    :return: a list of (index, elem) tuples of all elements in 'iterable' that share the maximum
        value. Note that a list is returned even if a single element has maximum value."""
    if isinstance(iterable, Mapping):
        iterator = iterable.iteritems()
    elif isinstance(iterable, Iterable):
        iterator = enumerate(iterable)
    else:
        raise TypeError("expected Mapping or Iterable")
    try:
        k, v = next(iterator)
    except StopIteration:
        raise ValueError("argument iterable must be non-empty")
    max_pairs = [(k, v)]
    max_key = v if key is None else key(v)
    for k, v in iterator:
        curr_key = v if key is None else key(v)
        if gt(curr_key, max_key):
            max_pairs = [(k, v)]
            max_key = curr_key
        elif eq(curr_key, max_key):
            max_pairs.append((k, v))
    return max_pairs


def min_pairs(iterable, key=None, lt=operator.lt, eq=operator.eq):
    """Like max_pairs(), but find minimum elements instead."""
    return max_pairs(iterable, key, lt, eq)


def max_values(iterable, key=None, gt=operator.gt, eq=operator.eq):
    """Based on max_pairs(), but returns elements of 'iterable' instead of (index, elem) pairs."""
    return [elem for _, elem in max_pairs(iterable, key, gt, eq)]


def min_values(iterable, key=None, lt=operator.lt, eq=operator.eq):
    """Same as max_values(), but for finding the minimum elements."""
    return [elem for _, elem in max_pairs(iterable, key, lt, eq)]


def max_keys(iterable, key=None, gt=operator.gt, eq=operator.eq):
    """Based on max_pairs(), but returns indices/keys in 'iterable' instead of (index, elem)
    pairs."""
    return [index for index, _ in max_pairs(iterable, key, gt, eq)]


def min_keys(iterable, key=None, lt=operator.lt, eq=operator.eq):
    """Same as max_keys(), but for finding the indices of minimum elements."""
    return [index for index, _ in max_pairs(iterable, key, lt, eq)]


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


def all_equal(iterable, key=None):
    """True iff all elements in 'iterable' are considered equal w.r.t. 'key'."""
    iterator = iter(iterable)
    try:
        elem = next(iterable)
    except StopIteration:
        raise ValueError("argument iterable must be non-empty")
    first_key = elem if key is None else key(elem)
    for elem in iterator:
        curr_key = elem if key is None else key(elem)
        if not curr_key == first_key:
            return False
    return True


def consume(iterable, n=float("inf")):
    """Consume the next 'n' elements in 'iterable'. Returns a 2-tuple with the iterator and the
    number of elements that were consumed."""
    iterator = iter(iterable)
    i = 0
    while i < n:
        try:
            next(iterator)
        except StopIteration:
            break
        i += 1
    return iterator, i


def consume_until(iterable, predicate=bool):
    """Consume elements from 'iterable' until 'predicate' is true. Returns a 2-tuple
    (iterator, elem), where iterator contains the remaining elements and elem is the first
    element found for which 'predicate' is true."""
    iterator = iter(iterable)
    for x in iterator:
        if predicate(x):
            return iterator, x
    raise StopIteration("unable to find element satisfying the given predicate")


def flat_iter(iterable, flatten=Iterable, depth=float("inf")):
    """Returns a flat iterator over the items of the argument 'iterable'. Only elements of
    iterable which are of the type(s) specified by 'flatten' (may be a single type or a tuple of
    types) are flattened. Note that these elements should at least be iterable (iter() is called
    on them). """
    stack = [iter(iterable)]
    while len(stack) > 0:
        it = stack[-1]
        try:
            elem = next(it)
        except StopIteration:
            stack.pop()
        else:
            recurse = (
                len(stack) <= depth and
                isinstance(elem, flatten) and
                not (isinstance(elem, basestring) and len(elem) == 1)
            )
            if recurse:
                stack.append(iter(elem))
            else:
                yield elem


def rotating_iter(iterable, size=2, step=1):
    """A rotating iterator. Yields tuples with 'size' contiguous elements from 'iterable', then
    moves forward 'step' elements, rotating out the older elements and replacing them with more
    recent elements. With default arguments, this iterates over consecutive pairs of elements in
    the argument 'iterable'.
    Note that if 'size' and 'step' are provided, the last few elements of 'iterable' may not be
    returned if its size is not equal to 'size + k * step', where 'k' is a non-negative integer.
    """
    it = iter(iterable)
    d = deque(islice(it, size), maxlen=size)
    if len(d) < size:
        return
    while True:
        yield tuple(d)
        for _ in xrange(step):
            try:
                x = next(it)
            except StopIteration:
                return
            else:
                d.append(x)


def interleaving_iter(*iterables):
    """A generator which interleaves the argument iterables (deals with uneven lengths)."""
    iterators = map(iter, iterables)
    index = 0
    # rotate through iterators until there is only one iterator remaining
    while len(iterators) > 1:
        iterator = iterators[index]
        try:
            yield next(iterator)
        except StopIteration:
            del iterators[index]
            index = index % len(iterators)
        else:
            index = (index + 1) % len(iterators)
    # yield all elements from the last iterator
    for elem in iterators[0]:
        yield elem

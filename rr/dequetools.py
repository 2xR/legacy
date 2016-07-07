"""
This module contains functions that extend the functionality of deque objects from the standard lib
collections module.

Usage:
    from collections import deque
    from rr import dequetools

    d = deque([1, "a", "b"])
    dequetools.insert(d, 2, "foo")
    print d
"""
from bisect import bisect_left, bisect_right


def _adjusted_index(sequence, index, extra_indices=0):
    if index < 0:
        index += len(sequence)
    if not 0 <= index < len(sequence) + extra_indices:
        raise IndexError("index out of range")
    return index


def insert(D, index, elem):
    """Insert 'elem' at index 'index'. Supports negative indices."""
    index = _adjusted_index(D, index, extra_indices=1)
    D.rotate(-index)
    D.appendleft(elem)
    D.rotate(index)


def pop(D, index=-1):
    """Pop and return the element at index 'index'. Supports negative indices."""
    index = _adjusted_index(D, index)
    elem = D[index]
    del D[index]
    return elem


def insort_left(D, elem):
    """Assuming deque 'D' is sorted, insert 'elem' in order *before* any elements that compare
    equal to it."""
    index = bisect_left(D, elem)
    insert(D, index, elem)


def insort_right(D, elem):
    """Assuming deque 'D' is sorted, insert 'elem' in order *after* any elements that compare
    equal to it."""
    index = bisect_right(D, elem)
    insert(D, index, elem)


insort = insort_right

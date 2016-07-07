from bisect import bisect_left, bisect_right


def fix_index(sequence, index, extend_index_range):
    if index < 0:
        index += len(sequence)
    if not 0 <= index < len(sequence) + extend_index_range:
        raise IndexError("index out of range")
    return index


def deque_insert(D, index, elem):
    """Insert 'elem' at index 'index'. Supports negative indices."""
    index = fix_index(D, index, 1)
    D.rotate(-index)
    D.appendleft(elem)
    D.rotate(index)


def deque_pop(D, index=-1):
    """Pop and return the element at index 'index'. Supports negative indices."""
    index = fix_index(D, index, 0)
    elem = D[index]
    del D[index]
    return elem


def deque_insort_left(D, elem):
    """Assuming deque 'D' is sorted, insert 'elem' in order *before* any elements that compare
    equal to it."""
    index = bisect_left(D, elem)
    deque_insert(D, index, elem)


def deque_insort_right(D, elem):
    """Assuming deque 'D' is sorted, insert 'elem' in order *after* any elements that compare equal
    to it."""
    index = bisect_right(D, elem)
    deque_insert(D, index, elem)


deque_insort = deque_insort_right

from __future__ import absolute_import

from copy import copy
from itertools import izip
from bisect import bisect_left, bisect_right

from utils.misc import callable_name, sorted_indices, INF, UNDEF
from utils.prettyrepr import prettify_class


@prettify_class
class SortedList(list):
    """A list of elements that are kept sorted by a specific key function. If 'maxlen' is defined,
    only the 'maxlen' elements with lowest key will be kept in the list. Note that the elements in
    the list are *always* in ascending order w.r.t. the key function. In order to reverse the
    order, one must specify a new key function that should be symmetrical to the original one."""
    __slots__ = ("_keys", "_key", "_maxlen")

    def __init__(self, iterable=None, key=None, maxlen=INF):
        list.__init__(self)
        if iterable is not None:
            list.extend(self, iterable)
        # "private" internal attributes
        self._keys = None
        self._key = UNDEF
        self._maxlen = None
        # initialize 'key' and 'maxlen' properties
        self.key = key
        self.maxlen = maxlen

    def __info__(self):
        key = "" if self._key is None else ("key=%s, " % callable_name(self._key))
        return "%smaxlen=%s, %s" % (key, self._maxlen, list.__repr__(self))

    def __copy__(self):
        """Create a shallow copy of the sorted list."""
        clone = SortedList.__new__(type(self))
        list.__setitem__(clone, slice(None), self)
        clone._keys = list(self._keys)
        clone._key = self._key
        clone._maxlen = self._maxlen
        return clone

    __getitem__ = list.__getitem__

    def __setitem__(self, i, v):
        raise NotImplementedError("cannot directly set items in sorted list. Use add() instead")

    def __setslice__(self, i, j, v):
        raise NotImplementedError("cannot directly set items in sorted list. Use add() instead")

    def __delitem__(self, i):
        list.__delitem__(self, i)
        keys = self._keys
        if keys is not None:
            del keys[i]

    def __delslice__(self, i, j):
        self.__delitem__(slice(i, j))

    @property
    def maxlen(self):
        return self._maxlen

    @maxlen.setter
    def maxlen(self, n):
        """Define a maximum length for the list, and discard the tail of the list if its size
        exceeds the specified length. Afterwards, when elements are add()ed, if the list is at its
        maximum size, the element is rejected if its key is >= to the key of the last element.
        Otherwise, the element is inserted and the last element is pop()'ed to keep the list from
        exceeding its maximum length."""
        if n < 1:
            raise ValueError("maxlen should be at least 1")
        self._maxlen = n
        if n < len(self):
            del self[n:]

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, key):
        """Set a new sorting key and re-sort the list. If the sort key is None, the list's elements
        themselves are used as keys."""
        if key is self._key:
            return
        self._key = key
        if key is None:
            self._keys = None
            list.sort(self)
        else:
            elems = list(self)
            keys = [key(elem) for elem in elems]
            indices = sorted_indices(keys)
            list.__setitem__(self, slice(None), [elems[i] for i in indices])
            self._keys = [keys[i] for i in indices]

    def pairs(self, *ijk):
        """pairs([start [, stop [, step]]]) - Returns the (item, key) pairs of the sorted list.
        Argument semantics identical to the builtin xrange() function. Like xrange(), this returns
        a generator, not a list."""
        if len(ijk) > 3:
            raise Exception("too many arguments: pairs([start [, stop [, step]]])")
        if len(ijk) == 3:
            start, stop, step = ijk
        elif len(ijk) == 2:
            start, stop, step = ijk[0], ijk[1], 1
        elif len(ijk) == 1:
            start, stop, step = 0, ijk[0], 1
        else:
            start, stop, step = 0, len(self), 1
        keys = self if self._keys is None else self._keys
        return izip(self[start:stop:step], keys[start:stop:step])

    def add(self, elem):
        """Add an element to the sorted list. The element is inserted in O(log(N)+2N) time in the
        worst case (i.e. item goes to the front of the list and everything must be moved back).
        If the list has a maxlen and is full, the element may not even be accepted into the list
        if its sort key is greater or equal to the key of the last element. If the element is
        accepted into the list, the last element is pop()ed if the list is at its maximum length.
        Returns True if the element was actually added to the list, False otherwise."""
        if self._key is None:
            key = elem
            keys = self
        else:
            key = self._key(elem)
            keys = self._keys
        if len(self) >= self._maxlen:
            if key >= keys[-1]:
                return False  # list is at maximum size, but the element cannot enter the list
            self.pop()
        index = bisect_right(keys, key)
        list.insert(self, index, elem)
        if keys is not self:
            keys.insert(index, key)
        return True

    def update(self, iterable):
        """Repeatedly call add() on the elements on iterable. Note that, if the list has a finite
        'maxlen', some of these elements may be added and then removed when adding subsequent
        elements."""
        add = self.add
        for elem in iterable:
            add(elem)

    def __iadd__(self, iterable):
        self.update(iterable)
        return self

    def __add__(self, iterable):
        return copy(self).__iadd__(iterable)

    def __mul__(self, n):
        raise NotImplementedError("undefined operation in sorted list")

    __imul__ = __mul__

    def remove(self, elem):
        """Remove an element from the list. Instead of a linear search as in a normal list, we take
        advantage of the fact that the list is sorted and find the element's index using binary
        search. This can lead to great performance improvement for large lists."""
        return self.pop(self.index(elem))

    def discard(self, elem):
        """Remove 'elem' if it is in the list, otherwise do nothing. Returns an (elem, key) pair."""
        try:
            index = self.index(elem)
        except ValueError:
            return None, None
        else:
            return self.pop(index)

    def pop(self, index=None):
        """Pop an index from the list. Returns a pair (elem, key). Note that if the list has no
        'key' function, the key will be the element itself, so the return value will effectively
        be (elem, elem)."""
        keys = self._keys
        if index is None:
            elem = list.pop(self)
            key = elem if keys is None else keys.pop()
        else:
            elem = list.pop(self, index)
            key = elem if keys is None else keys.pop(index)
        return (elem, key)

    def clear(self):
        """Remove all elements from the list."""
        del self[:]

    def __contains__(self, elem):
        """Membership testing also uses binary search for improved performance."""
        try:
            self.index(elem)
            return True
        except ValueError:
            return False

    def index(self, elem):
        """Uses binary search to find the index of the first occurrence of 'elem'. Binary search
        can be safely used since we're maintaining the list sorted, and this can lead to great
        performance improvements over linear search for large lists."""
        lo, hi = self.index_interval(elem)
        for i in xrange(lo, hi):
            if self[i] == elem:
                return i
        raise ValueError("element not found in %s" % type(self).__name__)

    def index_after(self, elem):
        """Perform a binary search on the list to find the index immediately after the last
        element with sorting key equal to 'elem's key."""
        if self._key is None:
            return bisect_right(self, elem)
        return bisect_right(self._keys, self._key(elem))

    def index_interval(self, elem):
        """Like index_after(), but returns two indices (i, j), such that i is the index of the
        first element with sorting key equal to 'elem's key, and j is the first index after all
        elements with equal key (same as index_after())."""
        j = self.index_after(elem)
        if self._key is None:
            i = bisect_left(self, elem, hi=j)
        else:
            i = bisect_left(self._keys, self._key(elem), hi=j)
        return (i, j)

    # --------------------------------------------------------------------------
    # Undefined/unavailable methods from list
    def append(self, elem):
        raise NotImplementedError("cannot append to sorted list. Use add() instead")

    def extend(self, elems):
        raise NotImplementedError("cannot extend sorted list. Use update() instead")

    def insert(self, index, elem):
        raise NotImplementedError("cannot insert items into sorted list. Use add() instead")

    def reverse(self):
        raise NotImplementedError("unable to reverse sorted list. Modify 'key' to change order")

    def sort(self, cmp=None, key=None, reverse=False):
        raise NotImplementedError("list is already sorted. Modify 'key' to change order")


def _test():
    text = """Text taken from Wikipedia:

        The Borda count is a single-winner election method in which voters rank candidates in order
    of preference. The Borda count determines the winner of an election by giving each candidate a
    certain number of points corresponding to the position in which he or she is ranked by each
    voter. Once all votes have been counted the candidate with the most points is the winner.
    Because it sometimes elects broadly acceptable candidates, rather than those preferred by the
    majority, the Borda count is often described as a consensus-based electoral system, rather than
    a majoritarian one.

    The Borda count was developed independently several times, but is named for the 18th-century
    French mathematician and political scientist Jean-Charles de Borda, who devised the system in
    1770. It is currently used for the election of two ethnic minority members of the National
    Assembly of Slovenia, [1] and, in modified forms, to apportionment of all seats in the
    Icelandic parliamentary elections and for selecting presidential election candidates in
    Kiribati, while also used to elect members of the Parliament of Nauru. It is also used
    throughout the world by various private organisations and competitions."""
    l = SortedList(set(text.split()))
    print "10 first words (alphabetically)", l[:10]
    l.key = len  # sort words by size (increasing)
    print "10 shortest words:", l[:10]
    l.key = lambda w: -len(w)  # sort words by size (decreasing)
    print "10 longest words:", l[:10]
    return l

from collections import Counter, Mapping, Iterable


class MultiSet(Counter):
    """Simple extension of collections.Counter with insert() and remove() methods (don't really
    understand why Counter doesn't have them...). Counter is just a misleading name for multiset
    or bag, a basic mathematical object (simply a set where items may appear more than once).

    This class now supports further operations that Counter does not, such as multiplication and
    division by a number, e.g.
        >>> x = MultiSet("abcbabcbacbacb")
        >>> y = x * 2
        >>> x *= 2
        >>> x == y
        True
        >>> x is y
        False
        >>> y /= 3
        >>> y == x / 3
        True

    Common set queries are available as well:
        - issuperset(): equivalently, >=
        - ispropersuperset(): equivalently, >
        - issubset(): equivalently, <=
        - ispropersubset(): equivalently, <

    TODO: write complete documentation
    """

    # --------------------------------------------------------------------------
    # Basic multiset manipulation methods. Elements are automatically removed
    # when their number of occurrences in the multiset is equal to zero.
    def insert(self, elem, n=1):
        """Adds 'n' occurrences of 'elem' to the multiset.

        If the number of occurrences of 'elem' in the set becomes zero, the object is removed.
        Returns the new number of occurrences of 'elem' in the multiset.

        NOTE: that unlike the builtin set type, the add() method of this class does the same as the
        update() method, i.e. add a batch of elements to the multiset. The method to add a single
        new element to the multiset is therefore (in my view more correctly) called insert()."""
        count = self[elem] + n
        if count == 0:
            self.pop(elem, None)
        else:
            self[elem] = count
        return count

    def remove(self, elem, n=1):
        return self.insert(elem, -n)

    def discard(self, elem):
        return self.pop(elem, None) is not None

    @property
    def size(self):
        """The total number of elements in the multiset. This is the sum of the values associated
        to all keys. Note that len() returns the number of different keys in the multiset."""
        return sum(self.itervalues())

    cardinality = size

    def ratio(self, other):
        """Returns how many times (a float) this multiset fully contains 'other'.

        This corresponds to the minimum of the ratios between the counts in 'self' and the counts
        in 'other' among all the keys in 'other' (excluding keys that have value == 0 in 'other').
        This method will raise ValueError if 'other' is empty or all its values are zero."""
        if not isinstance(other, Mapping):
            other = MultiSet(other)
        return min(float(self[elem]) / count for elem, count in other.iteritems() if count != 0)

    # --------------------------------------------------------------------------
    # add/update(), subtract/difference_update(), sum(), difference(), and operator overrides
    def update(self, collection=None, **kwargs):
        if collection is not None:
            if len(self) == 0 and isinstance(collection, Mapping):
                dict.update(self, collection)
            else:
                self.__apply(self.insert, collection)
        if len(kwargs) > 0:
            if len(self) == 0:
                dict.update(self, kwargs)
            else:
                self.__apply(self.insert, kwargs)
        return self

    __iadd__ = add = update

    def difference_update(self, collection=None, **kwargs):
        if collection is not None:
            self.__apply(self.remove, collection)
        if len(kwargs) > 0:
            self.__apply(self.remove, kwargs)
        return self

    __isub__ = subtract = difference_update

    def __apply(self, op, collection):
        if isinstance(collection, Mapping):
            for obj, n in collection.iteritems():
                op(obj, n)
        elif isinstance(collection, Iterable):
            for obj in collection:
                op(obj)
        else:
            raise TypeError("expected mapping or iterable object")

    def sum(self, collection=None, **kwargs):
        return self.copy().update(collection, **kwargs)

    __add__ = sum

    def difference(self, collection=None, **kwargs):
        return self.copy().difference_update(collection, **kwargs)

    __sub__ = difference

    # --------------------------------------------------------------------------
    # union and intersection
    def union_update(self, other):
        """Union is the maximum of value in either of the input multisets."""
        if not isinstance(other, Mapping):
            other = MultiSet(other)
        for elem, count in other.iteritems():
            self[elem] = max(self[elem], count)
        return self

    __ior__ = union_update

    def union(self, other):
        return self.copy().union_update(other)

    __or__ = __ror__ = union

    def intersection_update(self, other):
        """Intersection is the minimum of corresponding counts."""
        if not isinstance(other, Mapping):
            other = MultiSet(other)
        for elem, count in self.items():
            n = other.get(elem, 0)
            if n == 0:
                del self[elem]
            elif n < count:
                self[elem] = n
        return self

    __iand__ = intersection_update

    def intersection(self, other):
        return self.copy().intersection_update(other)

    __and__ = __rand__ = intersection

    # --------------------------------------------------------------------------
    # multiplication and division by scalars
    def multiply(self, n):
        for k in self.iterkeys():
            self[k] *= n
        return self

    __imul__ = multiply

    def __mul__(self, n):
        return self.copy().multiply(n)

    __rmul__ = __mul__

    def __idiv__(self, n):
        self.multiply(1.0 / n)
        return self

    def __div__(self, n):
        return self.copy().multiply(1.0 / n)

    # --------------------------------------------------------------------------
    # issuperset(), issubset() and companions
    def issuperset(self, other):
        if not isinstance(other, Mapping):
            other = MultiSet(other)
        return (len(self) >= len(other) and
                all(self[k] >= x for k, x in other.iteritems()))

    __ge__ = issuperset

    def issubset(self, other):
        if not isinstance(other, Mapping):
            other = MultiSet(other)
        return (len(self) <= len(other) and
                all(other.get(k, 0) >= x for k, x in self.iteritems()))

    __le__ = issubset

    def ispropersuperset(self, other):
        if not isinstance(other, Mapping):
            other = MultiSet(other)
        # If 'other' has more keys than 'self', 'self' is not a proper superset of 'other'.
        if len(self) < len(other):
            return False
        # If 'self' has more keys than 'other', 'self' *MAY BE* a proper superset of 'other'.
        # We must still verify for each key if the number of occurrences in 'self' is >=
        # the number of occurrences in 'other'. 'proper_subset' is true if either: 'self' has
        # more keys than 'other' and, for all keys in 'other', 'self' has the same number of
        # occurrences; OR 'self' has the same keys as 'other', has the same number of occurrences
        # as 'other' for all keys, except for *at least* one key of which 'self' has more
        # occurrences than 'other'. All this long and complicated text translates into this
        # concise beautiful piece of code :)
        proper_superset = len(self) > len(other)
        for k, x in other.iteritems():
            y = self[k]
            if y < x:
                return False
            if not proper_superset and y > x:
                proper_superset = True
        return proper_superset

    __gt__ = ispropersuperset

    def ispropersubset(self, other):
        # The ideas in this method are the same as in ispropersuperset().
        # Please refer to the comments on that function.
        if not isinstance(other, Mapping):
            other = MultiSet(other)
        if len(self) > len(other):
            return False
        proper_subset = len(self) < len(other)
        for k, x in self.iteritems():
            y = other.get(k, 0)
            if y < x:
                return False
            if not proper_subset and y > x:
                proper_subset = True
        return proper_subset

    __lt__ = ispropersubset


def example():
    m = MultiSet()
    sentence = "this is a simple test of the multiset module."
    for c in sentence:
        m.insert(c)
    print "Most common letters in %r:" % sentence
    for c, n in m.most_common():
        print "letter %r occurred %d times" % (c, n)
    return m


def test():
    """Tests suitable for running with pytest."""
    a = MultiSet("abc")
    b = MultiSet("def" * 2)

    assert a | b == MultiSet("abc" + "def" * 2)
    assert a & b == MultiSet()
    assert a * 2 == {"a": 2, "b": 2, "c": 2}
    assert b / 2 == {"d": 1, "e": 1, "f": 1}

    a.insert("d", 3)
    assert a & b == {"d": 2}
    assert a | b == {"a": 1, "b": 1, "c": 1,
                     "d": 3, "e": 2, "f": 2}

    assert a.ratio(b) == 0.0
    assert b.ratio(a) == 0.0
    b.update("abc")
    assert a.ratio(b) == 0.0
    assert b.ratio(a) == 2.0 / 3.0

from __future__ import absolute_import
import operator

from utils.prettyrepr import prettify_class


@prettify_class
class Pattern(object):
    """
    This class implements the Knuth-Morris-Pratt algorithm for finding the first match of a
    word/pattern in a sequence.
    Read wikipedia article for more information :P
    """
    __slots__ = ("W", "T", "match")

    def __init__(self, W, match=operator.eq):
        W = list(W)
        n = len(W)
        if n < 1:
            raise ValueError("expected non-empty pattern")
        # +++++++++++++++++++++++++++++++++++++++
        # construction of the partial match table
        T = None
        if n > 1:
            T = [None] * n
            T[0] = -1
            T[1] = 0
            i = 2
            j = 0
            while i < n:
                if match(W[j], W[i-1]):
                    j += 1
                    T[i] = j
                    i += 1
                elif j > 0:
                    j = T[j]
                else:
                    T[i] = 0
                    i += 1
        # +++++++++++++++++++++++++++++++++++++++
        # attribute initialization
        self.W = W
        self.T = T
        self.match = match

    def __info__(self):
        return "{}, match={}".format(self.W, self.match.__name__)

    def __iter__(self):
        return iter(self.W)

    def __len__(self):
        return len(self.W)

    def __getitem__(self, i):
        return self.W[i]

    def index_in(self, S, start=0, end=None):
        """Return the start index of the first occurrence of pattern 'W' in sequence 'S'. Returns
        None if the pattern is not contained in the sequence."""
        match = self.match  # predicate for matching elements in W and S
        W = self.W          # the pattern we're searching for
        T = self.T          # the table of partial matches (see above)
        n = len(W)          # size of the pattern
        m = start           # index pointing to the start of the match in S
        k = end if end is not None else len(S)  # index in S where we stop matching
        if k - m < n:  # the slice of S that we're searching is smaller than W
            return None
        if n == 1:  # W has only 1 element, so we simply traverse S and find its index
            w = W[0]
            for i in xrange(m, k):
                if match(w, S[i]):
                    return i
        else:      # pattern size is > 1, so we apply the actual KMP algorithm
            i = 0  # index of the element in W that we're currently comparing
            while m + i < k:
                if match(W[i], S[m+i]):
                    i += 1
                    if i == n:
                        return m
                else:
                    T_i = T[i]
                    m = m + i - T_i
                    i = max(0, T_i)
        return None


def search(W, S, start=0, end=None, match=None):
    """Search for pattern 'W' in sequence 'S'. This creates a Pattern object, uses it, and throws
    it away immediately. Returns the index of the first occurrence of 'W' in 'S', or None if the
    pattern does not exist in 'S'."""
    return Pattern(W, match).index_in(S, start, end)

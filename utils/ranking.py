from itertools import izip
from utils.sortedlist import SortedList

# ------------------------------------------------------------------------------
# Ranking method functions (to be used as the 'method' argument to ranking())
def standard_competition(rank, tied):
    """1224 ranking method"""
    return [rank] * tied, rank+tied
    
def modified_competition(rank, tied):
    """1334 ranking method"""
    return [rank+tied-1] * tied, rank+tied
    
def dense(rank, tied):
    """1223 ranking method"""
    return [rank] * tied, rank+1
    
def ordinal(rank, tied):
    """1234 ranking method"""
    return range(rank, rank+tied), rank+tied
    
def fractional(rank, tied):
    """1 2.5 2.5 4 ranking method"""
    return [sum(xrange(rank, rank+tied)) / float(tied)] * tied, rank+tied
    
# ------------------------------------------------------------------------------
# Main functions
def rank(items, key=None, reverse=False, method=standard_competition):
    """This function computes a ranking for a given set of items. The 'key' argument specifies 
    the ranking key, as in the builtin sorted() function. Also like sorted(), by default, ranks 
    are assigned to items in ascending order of key (i.e. items with lower key are placed at the 
    beginning of the ranking). Of course, this behavior can be inverted by using the 'reverse' 
    argument.
    
    Several methods can be used to compute the ranking when ties occur, possibly resulting in 
    different rankings for the same set of items (http://en.wikipedia.org/wiki/Ranking).
    The ranking method can be selected using the 'method' argument. Select one of 
        ranking.standard_competition (the default method)
        ranking.modified_competition
        ranking.dense
        ranking.ordinal
        ranking.fractional
        
    This function returns a list of 2-tuples (rank, item) sorted by rank."""
    # order items by key
    order = [((item if key is None else key(item)), item) for item in items]
    order.sort(key=(lambda p: p[0]), reverse=reverse)
    if len(order) == 0:
        return []
        
    ranking = []
    curr_rank = 1
    curr_tied = []
    curr_key = order[0][0]
    for key, item in order:
        # item is tied, add to set of tied items
        if key == curr_key:
            curr_tied.append(item)
        # new key, add previous set of tied items to the 
        # ranking and create a new set of tied items
        else:
            if len(curr_tied) == 1:
                ranking.append((curr_rank, curr_tied[0]))
                curr_rank += 1
            else:
                ranks, curr_rank = method(curr_rank, len(curr_tied))
                ranking.extend(izip(ranks, curr_tied))
            curr_tied = [item]
            curr_key = key
    # add the last tied elements to the ranking
    if len(curr_tied) == 1:
        ranking.append((curr_rank, curr_tied[0]))
    else:
        ranks, _ = method(curr_rank, len(curr_tied))
        ranking.extend(izip(ranks, curr_tied))
    return ranking
    
    
def first_n(iterable, n, key=None):
    """This function creates a sorted list with the first 'n' elements of 'iterable', using the 
    sorting key given by 'key'. If 'key' is None, the elements are used as their own sort keys."""
    items = list(iterable)
    l = SortedList(items if len(items) <= n else items[:n], key=key, maxlen=n)
    if len(items) > n:
        l.update(items[n:])
    return l
    
    
# ------------------------------------------------------------------------------
# Test code
def _test():
    I = "a b b c".split()
    M = [standard_competition, modified_competition, dense, ordinal, fractional]
    R = [rank(I, method=m) for m in M]
    print "Ranking items:", I
    for m, r in zip(M, R):
        print m.__name__, "-->", r
        
        

"""The functions in this module typically receive a digraph as argument. The conventioned format
for digraphs is a dictionary with vertices 'v' as keys, and their outgoing arcs defined by internal
dictionaries. To each key 'w' in these dictionaries corresponds an arc '<v,w>', and the weight of
the arc is defined by the value associated to 'w'. Alternatively, outgoing arcs leaving vertex 'v'
can be defined as an iterable containing a set of vertices. Each arc is then considered to have
weight 1.
Example:
    G = {"a": {"b": 2, "c": 1, "d": 4},  # here the weights are explicitly defined
         "b": ["a", "c", "d"],           # here the weights are implicitly 1
         "c": [],                        # a vertex without outgoing arcs
         "d": MultiSet(a=2, c=3)}        # outgoing arcs defined as a MultiSet object
"""
from itertools import izip, repeat
from utils.misc import UNDEF


def vertices(G):
    """An iterator over the vertices of graph G."""
    return G.iterkeys()


def arcs(G):
    """An iterator over the arcs of graph G. Yields (v, w, weight) tuples."""
    for v, A_v in G.iteritems():
        if isinstance(A_v, dict):
            for w, weight in A_v.iteritems():
                yield v, w, weight
        else:
            for w in A_v:
                yield v, w, 1


def has_arc(G, v, w):
    """Return a boolean indicating whether the arc (v, w) exists in the graph."""
    return w in G[v]


def indegree(G):
    """Given a digraph, compute the indegree of each vertex. The indegree of a vertex is simply the
    sum of the weights of all arcs ending at that particular vertex."""
    indeg = {v: 0 for v in G}
    for v, A_v in G.iteritems():
        if isinstance(A_v, dict):
            for w, weight in A_v.iteritems():
                indeg[w] += weight
        else:
            for w in A_v:
                indeg[w] += 1
    return indeg


def outdegree(G):
    """Compute the outdegree of each vertex in G."""
    outdeg = {v: 0 for v in G}
    for v, A_v in G.iteritems():
        if isinstance(A_v, dict):
            outdeg[v] += sum(A_v.itervalues())
        else:
            outdeg[v] += len(A_v)
    return outdeg


def reversed(G):
    """Given a digraph G, create a graph with the same set of vertices but with inverted arcs."""
    R = {v: {} for v in G.iterkeys()}
    for v, A_v in G.iteritems():
        if isinstance(A_v, dict):
            for w, weight in A_v.iteritems():
                R[w][v] = weight
        else:
            for w in A_v:
                # here we add the weights because the sequence can have
                # repeated elements to represent multiple arcs from v to w
                R_w = R[w]
                R_w[v] = R_w.get(v, 0) + 1
    return R


def toposort(G, key=UNDEF):
    """Topologically sort a directed graph. This function raises ValueError if the graph contains
    cycles, since it is not possible to compute a topological order of its vertices. Otherwise, it
    returns a list of its vertices sorted in one possible topological order. Note that a digraph
    may have multiple topological orders. However, this function will always return the same order
    across different calls if the same arguments are provided.
    To have some control over the sequence that is produced by this function, a 'key' function can
    be passed as argument. The key function is used with the built-in min() function to obtain the
    next vertex in the sequence.
        - If 'key' is UNDEF, min() is not called and an arbitrary element is selected.
        - If 'key' is None, min() is called without a key function, i.e. the vertices themselves
        are used as key.
        - Otherwise, min() is called with the argument key function, allowing fine control over the
        sequence."""
    indeg = indegree(G)
    sources = {v for v, indeg_v in indeg.iteritems() if indeg_v == 0}
    order = []
    for _ in xrange(len(G)):
        # check if there are vertices with indegree equal to zero
        if len(sources) == 0:
            raise ValueError("toposort failed: all remaining vertices have indegree > 0")
        if key is UNDEF:
            v = sources.pop()
        else:
            v = min(sources) if key is None else min(sources, key=key)
            sources.remove(v)
        # add v to the sequence and update the indegree of its successors
        order.append(v)
        A_v = G[v]
        A_v = A_v.iteritems() if isinstance(A_v, dict) else izip(A_v, repeat(1, len(A_v)))
        for w, weight in A_v:
            indeg_w = indeg[w] = indeg[w] - weight
            if indeg_w == 0:
                sources.add(w)
    return order


def is_symmetric(G):
    """A digraph is symmetric if for every arc (v, w) it contains the reversed arc (w, v)."""
    # create a set of arcs excluding self-loops
    A = {(v, w) for v, w, weight in arcs(G) if v != w}
    # obviously the number of arcs should be even
    if len(A) % 2 == 1:
        return False
    while len(A) > 0:
        # in each iteration we drop a pair of symmetric arcs until
        # we have no arcs left or we find an arc without a pair
        v, w = A.pop()
        try:
            A.remove((w, v))
        except KeyError:
            return False
    return True


def is_dag(G):
    """A digraph is acyclic if it is possible to sort it topologically."""
    try:
        toposort(G)
    except ValueError:
        return False
    return True


def random_digraph(vertices=10000, max_arcs_per_node=100, acyclic=False, seed=None):
    from random import seed as set_seed, sample, randrange
    if seed is not None:
        set_seed(seed)
    n = vertices
    a = min(max_arcs_per_node, vertices)
    G = {}
    for v in xrange(n):
        population = xrange(v+1, n) if acyclic else xrange(n)
        sample_size = randrange(min(n-v, a)) if acyclic else randrange(a)
        G[v] = sample(population, sample_size)
    return G


G = {2:  [],
     3:  [8, 10],
     5:  [11],
     7:  [8, 11],
     8:  [9],
     9:  [],
     10: [],
     11: [2, 9, 10]}


# def tarjan(G):
#     S = set()
#     i = 0
#     index = {}
#     for v in G.iterkeys():
#         if v not in index:
#             strongconnect(G, v, index)

# def strongconnect(v):
#     # Set the depth index for v to the smallest unused index
#     index[v] = i
#     lowlink[v] = i
#     i += 1
#     S.add(v)

#     # Consider successors of v
#     for w in G[v]:
#        if w not in index:
#          # Successor w has not yet been visited; recurse on it
#         strongconnect(w)
#         lowlink[v] = min(lowlink[v], lowlink[w])
#       elif w in S:
#          # Successor w is in stack S and hence in the current SCC
#          lowlink[v]  = min(lowlink[v], w.index)


#     # If v is a root node, pop the stack and generate an SCC
#     if lowlink[v] == index[v]:
#         start a new strongly connected component
#         repeat
#             w = S.pop()
#             add w to current strongly connected component
#         until (w = v)
#         output the current strongly connected component

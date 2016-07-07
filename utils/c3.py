def default_get_bases(cls):
    return cls.__bases__


def default_get_subs(cls):
    return cls.__subclasses__()


def default_get_ro(cls):
    return cls.__mro__


def linearization(c, get_bases=default_get_bases, get_ro=default_get_ro):
    """Compute an inheritance order (or field lookup sequence) for c. We use the C3 linearization
    algorithm as explained in http://www.python.org/download/releases/2.3/mro/.
    Note that c does not have to be a class. In fact, c can be anything where multiple inheritance
    may be useful."""
    B = list(get_bases(c))
    if len(B) == 0:
        tail = []
    elif len(B) == 1:
        tail = list(get_ro(B[0]))
    else:
        tail = _merge(_master_list(B, get_ro))
    return [c] + tail


def update_order(c, get_subs=default_get_subs):
    """This function computes the order by which linearizations should be recomputed when the bases
    of 'c' are modified (either adding or removing elements). The order can be given by a simple
    topological sort of the inheritance graph starting at 'c'."""
    D = {}
    stack = [(c, 0)]
    while len(stack) > 0:
        c, d = stack.pop()
        if d > D.get(c, -1):
            D[c] = d
            d += 1
            stack.extend((x, d) for x in get_subs(c))
    return sorted(D.iterkeys(), key=D.__getitem__)


def _master_list(B, get_ro):
    """First we create a list of lists of "classes" (anything, actually), containing the MROs of
    all bases plus our list of bases at the end."""
    L_master = []
    if len(B) > 0:
        if len(set(id(b) for b in B)) != len(B):
            raise Exception("duplicate bases not allowed")
        for b in B:
            L_master.append(list(get_ro(b)))
        L_master.append(B)
    return L_master


def _merge(L_master):
    """This is where the magic happens :) In this function we actually build the RO (resolution
    order) list."""
    ro = []
    while len(L_master) > 0:
        c = _eligible_head(L_master)  # search for an eligible head c
        _purge_head(c, L_master)      # remove c from all sublists
        ro.append(c)                  # append c to the resolution order
    return ro


def _eligible_head(L_master):
    """Search the master list for an eligible head of a sublist. Only eligible heads can be legally
    added to the MRO. For c to be eligible for linearization, it can only appear as the head, or
    not appear at all, in any sub-list. If it is found in the tail of any sub-list, then it is not
    eligible for insertion into the MRO."""
    H = set()  # set of ids of visited sublist heads
    for L in L_master:
        h = L[0]
        if id(h) in H:  # no need to search the same head twice
            continue
        for M in L_master:
            if M is L:
                continue
            try:
                i = M.index(h)
            except ValueError:
                pass
            else:
                if i > 0:
                    break
        else:  # entered when the inner for loop is exhausted
            return h
        H.add(id(h))  # add to the set of searched heads
    raise Exception("ambiguous hierarchy (unable to find eligible head)")


def _purge_head(c, L_master):
    """Remove all occurrences of c from the master list L_master (note that c can only appear as
    the head of any sub-list), getting rid of any sub-lists that become empty from eliminating c.
    """
    i = 0
    while i < len(L_master):
        L_i = L_master[i]
        if L_i[0] is c:
            if len(L_i) == 1:
                del L_master[i]  # remove sub-list from "master" list
                continue
            else:
                del L_i[0]       # remove head of sub-list
        i += 1


def _test1():
    O = object
    class F(O): pass
    class E(O): pass
    class D(O): pass
    class C(D,F): pass
    class B(D,E): pass
    class A(B,C): pass
    assert linearization(A) == [A, B, C, D, E, F, O]


def _test2():
    O = object
    class A(O): pass
    class B(O): pass
    class C(O): pass
    class D(O): pass
    class E(O): pass
    class K1(A,B,C): pass
    class K2(D,B,E): pass
    class K3(D,A):   pass
    class Z(K1,K2,K3): pass
    assert linearization(Z) == [Z, K1, K2, K3, D, A, B, C, E, O]

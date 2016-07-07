from __future__ import absolute_import

from collections import namedtuple

from utils.copy import deepcopy_into
from utils.multiset import MultiSet


DomainUpdate = namedtuple("DomainUpdate", "hide_count, hide_delta")


class EmptyDomain(Exception):
    """Exception raised when a domain becomes empty after withdrawing values."""
    pass


class FiniteDomain(set):
    """A very simple class for *unordered* finite domains. Values can be hidden and unhidden using
    hide(), unhide(), hide_many() and unhide_many(). To withdraw an element from the domain (like a
    stronger version of hide), withdraw() should be used. Withdrawn elements only reappear in the
    domain when it is restored, as opposed to hidden elements which may be unhidden at any time.
    Domain state can be stored in a stack using save(), and later restored using restore()."""
    Empty = EmptyDomain

    def __init__(self, iterable=()):
        set.__init__(self, iterable)
        self.hidden = MultiSet()
        self.withdrawn = set()
        self.stack = []
        self.save()

    deepcopy = deepcopy_into

    def __hash__(self):
        """Make domains hashable (this means we can have sets of domains and dictionaries with
        domain keys). Note that two domains with the same elements will hash differently, but
        traditional set comparison operators work as expected, i.e.
            fd1 = FiniteDomain(range(5))
            fd2 = FiniteDomain(range(5))
            fd1 is not fd2 and hash(fd1) != hash(fd2) and fd1 == f2."""
        return id(self)

    def __eq__(self, other):
        if isinstance(other, FiniteDomain):
            return (set.__eq__(self, other) and
                    self.hidden == other.hidden and
                    self.withdrawn == other.withdrawn and
                    self.stack == other.stack)
        else:
            return set.__eq__(self, other)

    def __repr__(self):
        return "%s{%s}" % (type(self).__name__, ", ".join(repr(elem) for elem in self))

    def details(self, separator="\n\t", display=True):
        parts = [repr(self), "hidden=%s" % (self.hidden,), "withdrawn=%s" % (self.withdrawn,)]
        details = separator.join(parts)
        if display:
            print details
        else:
            return details

    def hide(self, elem):
        """Hide an element from the domain, so that it is no longer considered a candidate value
        for a given variable."""
        if elem in self or elem in self.hidden:
            if self.hidden.insert(elem) == 1:
                self.remove(elem)
            self.stack[-1].hide_delta.insert(elem)
        elif elem in self.withdrawn:
            raise ValueError("element is withdrawn")
        else:
            raise ValueError("element is not a member of the domain")

    def unhide(self, elem):
        """Unhide a hidden element."""
        if elem in self.hidden:
            if self.hidden.remove(elem) == 0:
                self.add(elem)
            self.stack[-1].hide_delta.remove(elem)
        elif elem in self:
            raise ValueError("element is already unhidden")
        elif elem in self.withdrawn:
            raise ValueError("element is withdrawn")
        else:
            raise ValueError("element is not a member of the domain")

    def withdraw(self, elem):
        """Permanently hide an element from the domain. The element only becomes available again
        after a restore(). Furthermore, an exception is raised if the domain becomes empty after
        withdrawing the element."""
        if elem in self or elem in self.hidden:
            hide_count, hide_delta = self.stack[-1]
            elem_hide_count = self.hidden[elem]
            elem_hide_delta = hide_delta[elem]
            # record the element's hide count at the previous saved state instead of its current
            # hide count, since when we restore() later we'll want that state to be restored
            hide_count[elem] = elem_hide_count - elem_hide_delta
            if elem_hide_delta != 0:
                del hide_delta[elem]
            self.withdrawn.add(elem)
            (self.remove if elem_hide_count == 0 else self.hidden.pop)(elem)
            if len(self) + len(self.hidden) == 0:
                raise EmptyDomain("all elements are withdrawn")
        elif elem in self.withdrawn:
            raise ValueError("element is already withdrawn")
        else:
            raise ValueError("element is not a member of the domain")

    def hide_many(self, elems):
        for elem in elems:
            self.hide(elem)
        return elems

    def unhide_many(self, elems):
        for elem in elems:
            self.unhide(elem)
        return elems

    def withdraw_many(self, elems):
        for elem in elems:
            self.withdraw(elem)
        return elems

    def save(self):
        """Save the current state of the domain, so that a later call to restore() will unhide/hide
        any values hidden/unhidden in-between the calls to save() and restore(). This method
        appends a new state to the domain's state stack."""
        self.stack.append(DomainUpdate(MultiSet(), MultiSet()))

    def restore(self, pop_stack=True):
        """Restore the domain's state to the last saved state, i.e. hide/unhide any values
        unhidden/hidden since the last call to save(). This is the only way that withdrawn values
        are made available again, since there is no 'unwithdraw()' method."""
        hide_count, hide_delta = self.stack[-1]
        for elem, n in hide_count.iteritems():
            self.withdrawn.remove(elem)
            if n == 0:
                self.add(elem)
            else:
                self.hidden[elem] = n
        for elem, n in hide_delta.iteritems():
            if self.hidden.remove(elem, n) == 0:
                self.add(elem)
            else:
                self.discard(elem)
        if pop_stack and len(self.stack) > 1:
            self.stack.pop()
        else:
            hide_count.clear()
            hide_delta.clear()

    def reset(self):
        """restore the domain back to its initial state, also clearing the stack of saved states."""
        self.update(self.withdrawn)
        self.update(self.hidden)
        self.hidden.clear()
        self.withdrawn.clear()
        self.stack = []
        self.save()


def _test():
    d = FiniteDomain(xrange(5))
    assert d == set([0, 1, 2, 3, 4])

    d.hide(3)
    assert d == set([0, 1, 2, 4])

    d.hide(2)
    assert d == set([0, 1, 4])

    d.hide_many([0, 1, 2, 4, 3, 3])
    assert len(d) == 0
    assert dict(d.hidden) == {0: 1, 1: 1, 2: 2, 3: 3, 4: 1}

    d.restore()
    assert d == set([0, 1, 2, 3, 4])

    d.hide(1)
    d.save()
    assert d == set([0, 2, 3, 4])

    d.hide(2)
    d.unhide(1)
    assert d == set([0, 1, 3, 4])

    d.restore()
    assert d == set([0, 2, 3, 4])

    d.restore()
    assert d == set([0, 1, 2, 3, 4])
    return d

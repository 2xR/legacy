"""
Actions provide an intuitive way to create simple "scripts" to run inside a kivy application. An
action can be a sequence of callbacks and delays for example.
"""
from kivy.clock import Clock

from utils.prettyrepr import prettify_class


@prettify_class
class Action(object):
    def __init__(self, parent=None):
        self.parent = None
        if parent is not None:
            parent.add(self)

    def start(self):
        pass

    def finished(self):
        print "Finished:", self
        if self.parent is not None:
            self.parent.child_finished(self)


class Call(Action):
    __info_attrs__ = ("callable",)

    def __init__(self, callable, parent=None):
        Action.__init__(self, parent)
        self.callable = callable

    def start(self):
        self.callable()
        self.finished()


class Wait(Action):
    __info_attrs__ = ("dt",)

    def __init__(self, dt, parent=None):
        Action.__init__(self, parent)
        self.dt = dt

    def start(self):
        Clock.schedule_once(self._finished, self.dt)

    def _finished(self, dt):
        self.finished()


class CompoundAction(Action):
    __info_attrs__ = ("children",)
    children = None

    def child_finished(self):
        raise NotImplementedError()


class Sequence(CompoundAction):
    def __init__(self, children=(), parent=None):
        CompoundAction.__init__(self, parent)
        self.children = []
        self.current = None
        self.remaining = None
        for child in children:
            self.add(child)

    def add(self, child, index=None):
        if self.current is not None:
            raise Exception("cannot modify sequence while it is running")
        if child.parent is not None:
            raise ValueError("child action already has a parent")
        if index is None:
            self.children.append(child)
        else:
            self.children.insert(index, child)
        child.parent = self

    def start(self):
        if self.current is not None:
            raise Exception("sequence has already been started")
        self.remaining = iter(self.children)
        self.current = self.remaining.next()
        self.current.start()

    def child_finished(self, child):
        if child is not self.current:
            raise ValueError("argument action is not the current child")
        try:
            self.current = self.remaining.next()
        except StopIteration:
            self.remaining = None
            self.current = None
            self.finished()
        else:
            self.current.start()


def add_op(a, b):
    if isinstance(a, Sequence):
        a.add(b)
        return a
    elif isinstance(b, Sequence):
        b.add(a, index=0)
    else:
        return Sequence([a, b])


Action.__add__ = add_op

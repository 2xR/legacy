import operator
from kivy.animation import Animation as BaseAnimation
from kivy.event import EventDispatcher

from utils.prettyrepr import prettify_class


@prettify_class
class Rel(object):
    op = None

    def __init__(self, value):
        self.value = value

    def __info__(self):
        return self.value

    def apply_to(self, x):
        return self.op(x, self.value)


class RelAdd(Rel):
    op = operator.add


class RelMul(Rel):
    op = operator.mul


Rel.add = RelAdd
Rel.mul = RelMul


class Animation(BaseAnimation):
    def _initialize(self, widget):
        BaseAnimation._initialize(self, widget)
        props = self._widgets[widget.uid]["properties"]
        rel_props = {}
        for p, (v0, v1) in props.iteritems():
            if isinstance(v1, Rel):
                rel_props[p] = (v0, v1.apply_to(v0))
        props.update(rel_props)

    def bound_to(self, widget):
        return BoundAnimation(self, widget)


class BoundAnimation(EventDispatcher):
    __events__ = ("on_start", "on_progress", "on_complete", "on_cancel")
    __ongoing = set()  # this is used to keep objects alive while they're running

    def __init__(self, anim, widget):
        EventDispatcher.__init__(self)
        self.anim = anim
        self.widget = widget
        self.anim.bind(on_start=self._anim_started,
                       on_progress=self._anim_progress,
                       on_complete=self._anim_completed)

    @property
    def duration(self):
        return self.anim.duration

    @property
    def transition(self):
        return self.anim.transition

    def start(self):
        self.anim.start(self.widget)

    def stop(self):
        self.anim.stop(self.widget)

    def cancel(self):
        self.anim.cancel(self.widget)
        self.dispatch("on_cancel")

    def on_start(self):
        BoundAnimation.__ongoing.add(self)

    def on_progress(self, progress):
        pass

    def on_complete(self):
        BoundAnimation.__ongoing.remove(self)

    def on_cancel(self):
        BoundAnimation.__ongoing.remove(self)

    def _anim_started(self, anim, widget):
        self.dispatch("on_start")

    def _anim_progress(self, anim, widget, progress):
        self.dispatch("on_progress", progress)

    def _anim_completed(self, anim, widget):
        self.dispatch("on_complete")

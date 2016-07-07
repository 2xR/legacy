from math import pi

from kivyx.widgets import Image, Transform
from kivyx.resources import resource_find
from kivyx.lib import Vector

from physix.bodyeditor.tools.transform.mode import TransformMode
from physix.bodyeditor.edithistory import Resize


class Extender(Transform, TransformMode):
    X_AXIS = 0
    Y_AXIS = 1
    AXES = (X_AXIS, Y_AXIS)
    POSITIVE = +1
    NEGATIVE = -1
    DIRECTIONS = (POSITIVE, NEGATIVE)
    ROTATION_MAP = {(X_AXIS, POSITIVE): 0.0,
                    (X_AXIS, NEGATIVE): pi,
                    (Y_AXIS, POSITIVE): pi / 2.0,
                    (Y_AXIS, NEGATIVE): -pi / 2.0}
    ALIGNMENT_MAP = {(X_AXIS, POSITIVE): (("viewport_right", "right"),
                                          ("viewport_center_y", "center_y")),
                     (X_AXIS, NEGATIVE): (("viewport_x", "x"),
                                          ("viewport_center_y", "center_y")),
                     (Y_AXIS, POSITIVE): (("viewport_center_x", "center_x"),
                                          ("viewport_top", "top")),
                     (Y_AXIS, NEGATIVE): (("viewport_center_x", "center_x"),
                                          ("viewport_y", "y"))}

    def __init__(self, axis, direction):
        if axis not in (0, 1):
            raise ValueError("unknown axis")
        if direction not in (-1, +1):
            raise ValueError("unknown direction")
        Transform.__init__(self)
        TransformMode.__init__(self)
        self._build()
        self.axis = axis
        self.direction = direction
        self.rotation = Extender.ROTATION_MAP[axis, direction]
        self.pivot_relpoint = Vector(0.5, 0.5)
        self.pivot_relpoint[axis] -= 0.5 * direction
        self.initial_size = None
        self.initial_pos = None

    def _build(self):
        filepath = resource_find("extend.png")
        self.image = Image(source=filepath, allow_stretch=True, keep_ratio=True)
        self.bind(viewport_size=self.image.setter("size"))
        self.add_widget(self.image)

    def attach_to(self, widget):
        TransformMode.attach_to(self, widget)
        widget.add_widget(self)
        widget.bind(viewport_size=self.resize_and_realign)
        self.resize_and_realign(widget, widget.viewport_size)

    def detach(self):
        self.target.unbind(viewport_size=self.resize_and_realign)
        self.target.remove_widget(self)
        TransformMode.detach(self)

    def resize_and_realign(self, widget, size):
        self.viewport_size = [0.2 * min(size)] * 2
        for p1, p2 in Extender.ALIGNMENT_MAP[self.axis, self.direction]:
            setattr(self, p2, getattr(widget, p1))

    def on_touch_down(self, touch):
        self.initial_size = self.target.viewport_size
        self.initial_pos = self.target.pos

    def on_touch_move(self, touch):
        # find the original coordinates of the pivot
        widget = self.target
        pivot = Vector(widget.viewport_pos) + Vector(widget.viewport_size) * self.pivot_relpoint
        x0, y0 = widget.to_parent(*pivot)
        # resize the object
        axis = self.axis
        size = list(widget.viewport_size)
        touch_pos_local = widget.to_local(*touch.pos)
        size[axis] = abs(pivot[axis] - touch_pos_local[axis])
        widget.viewport_size = size
        # move the object such that the pivot goes back to its original coordinates
        pivot = Vector(widget.viewport_pos) + Vector(widget.viewport_size) * self.pivot_relpoint
        x1, y1 = widget.to_parent(*pivot)
        widget.do_translate(x0 - x1, y0 - y1)

    def on_touch_up(self, touch):
        widget = self.target
        if widget.viewport_size != self.initial_size or widget.pos != self.initial_pos:
            command = Resize(widget, self.initial_size, self.initial_pos,
                             widget.viewport_size, widget.pos)
            touch.ud.editor.history.append(command)

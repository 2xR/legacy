from math import atan2

from kivyx.widgets import Image
from kivyx.resources import resource_find

from physix.bodyeditor.tools.transform.mode import TransformMode
from physix.bodyeditor.edithistory import Rotate


class Rotator(Image, TransformMode):
    ALIGNMENT = (("viewport_x", "x"), ("viewport_top", "top"))

    def __init__(self):
        filepath = resource_find("rotate.png")
        Image.__init__(self, source=filepath, allow_stretch=True, keep_ratio=True)
        TransformMode.__init__(self)
        self.initial_rotation = None
        self.offset = None

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
        self.size = [0.2 * min(size)] * 2
        for p1, p2 in Rotator.ALIGNMENT:
            setattr(self, p2, getattr(widget, p1))

    def on_touch_down(self, touch):
        self.initial_rotation = self.target.rotation
        lx, ly = self.target.to_local(touch.x, touch.y)
        self.offset = atan2(ly, lx)

    def on_touch_move(self, touch):
        cx, cy = self.target.center
        alpha = atan2(touch.y - cy, touch.x - cx)
        self.target.rotation = alpha - self.offset

    def on_touch_up(self, touch):
        widget = self.target
        if widget.rotation != self.initial_rotation:
            command = Rotate(widget, self.initial_rotation, widget.rotation)
            touch.ud.editor.history.append(command)

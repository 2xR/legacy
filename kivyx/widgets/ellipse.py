from kivy.uix.widget import Widget
from kivy.graphics import Ellipse as EllipseGfx

from kivyx.widgets.colorable import ColorableMixin
from kivyx.misc import bind_geometry


class Ellipse(Widget, ColorableMixin):
    def __init__(self, **kwargs):
        Widget.__init__(self, **kwargs)
        ColorableMixin.init(self)
        with self.canvas:
            self._gfx = EllipseGfx(pos=self.pos, size=self.size)
            bind_geometry(self._gfx, self)

from kivy.uix.widget import Widget
from kivy.graphics import Rectangle as RectangleGfx

from kivyx.widgets.colorable import ColorableMixin
from kivyx.misc import bind_geometry


class Rectangle(Widget, ColorableMixin):
    def __init__(self, **kwargs):
        Widget.__init__(self, **kwargs)
        ColorableMixin.init(self)
        with self.canvas:
            self._gfx = RectangleGfx(pos=self.pos, width=self.width, height=self.height)
            bind_geometry(self._gfx, self)

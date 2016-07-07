from kivyx.widgets import Widget
from kivyx.properties import ObjectProperty
from kivyx.links import Link

from physix.worldeditor.surface import Surface
from physix.worldeditor.sidebar import Sidebar
from physix.common import Statusbar


class WorldEditor(Widget):
    surface = ObjectProperty(None)
    statusbar = ObjectProperty(None)
    sidebar = ObjectProperty(None)

    def __init__(self):
        Widget.__init__(self)
        self._build()

    def _build(self):
        self.statusbar = Statusbar(self)
        self.surface = Surface(self)
        self.sidebar = Sidebar(self)

        self.add_widget(self.surface)
        self.add_widget(self.statusbar)
        self.add_widget(self.sidebar)

        Link(self.surface, size=((0.80, 0.95), self),
             align_xy=(Link.TOP, self))
        Link(self.sidebar, size=((0.2, 0.95), self), align_xy=(Link.TOP_LEFT, self.surface,
             Link.TOP_RIGHT))
        Link(self.statusbar, size=((1.0, 0.05), self),
             align_xy=(Link.BOTTOM, self))

    def clear(self):
        self.surface.clear_objects()
        self.surface.draw_origin()

    reset = clear

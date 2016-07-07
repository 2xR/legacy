from math import hypot

from utils.prettyrepr import prettify_class
from kivyx.widgets import Circle

from physix.common import EditorObject
from physix.common.physics import DENSITY, FRICTION, RESTITUTION, SENSOR


@prettify_class
@EditorObject.register_class
class EditorCircle(EditorObject):
    __info_attrs__ = ["center", "size"]

    registry_key = "circle"
    spec_attrs = EditorObject.spec_attrs + ("viewport_size", "center", "rgba", "physics")
    settings = EditorObject.settings + [DENSITY, FRICTION, RESTITUTION, SENSOR]
    rotatable = False

    def __init__(self):
        EditorObject.__init__(self)
        self.circle = Circle()
        self.add_widget(self.circle)
        self.prev_viewport_size = self.viewport_size
        self.bind(viewport_width=self.circle.setter("width"),
                  viewport_pos=self.circle.setter("pos"),
                  rgba=self.circle.setter("rgba"))

    def on_viewport_size(self, widget, size):
        """This dirty trick is necessary to keep the widget square... Couldn't figure out a more
        elegant way to do this o_O (the way we used on kivyx.widgets.circle doesn't seem to work
        here for some strange reason)."""
        prev_w, prev_h = self.prev_viewport_size
        curr_w, curr_h = size
        self.prev_viewport_size = size
        if curr_w != prev_w:
            self.viewport_height = curr_w
        elif curr_h != prev_h:
            self.viewport_width = curr_h

    def collide_point(self, x, y):
        """Make perfect point collisions with the circle. The default was an AABB collision that
        allowed picking the circle by clicking outside of it."""
        return distance(self.center, (x, y)) <= self.viewport_width * 0.5


def distance((x0, y0), (x1, y1)):
    """Euclidean distance between two points."""
    return hypot(x1-x0, y1-y0)

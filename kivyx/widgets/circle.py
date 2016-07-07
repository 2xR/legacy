from math import hypot

from kivy.properties import AliasProperty
from kivyx.widgets.ellipse import Ellipse


class Circle(Ellipse):
    """This is just an ellipse that keeps its width linked to its height. It also has a 'radius'
    property that is equal to half its width.
    WARNING: do NOT add this into a layout widget (or anything that tries to adjust the size of the
    circle automatically), or seriously wacky shit may go down (a.k.a. the layout and the circle
    will fight to resize the circle the way each one wants)."""
    def on_width(self, widget, w):
        if self.height != w:
            self.height = w

    def on_height(self, widget, h):
        if self.width != h:
            self.width = h

    def _get_radius(self):
        return self.width * 0.5

    def _set_radius(self, radius):
        self.width = 2.0 * radius

    radius = AliasProperty(_get_radius, _set_radius, bind=["width"])

    del _get_radius
    del _set_radius

    def collide_point(self, x, y):
        cx, cy = self.center
        return hypot(x - cx, y - cy) <= self.width * 0.5

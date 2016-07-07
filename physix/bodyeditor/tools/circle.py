from math import hypot
from random import random

from physix.bodyeditor.tools.geometry import GeometryTool
from physix.bodyeditor.objects import EditorCircle


class CircleTool(GeometryTool):
    MIN_RADIUS = 0.05
    button_text = "Circle"

    def new_widget(self):
        widget = EditorCircle()
        widget.hsv = (random(), 1.0, 1.0)
        widget.viewport_size = (1e-9, 1e-9)
        widget.center = self.init_pos
        return widget

    def update_widget(self, widget):
        diameter = 2.0 * distance(self.curr_pos, self.init_pos)
        widget.viewport_size = (diameter, diameter)
        widget.center = self.init_pos

    def valid_widget(self, widget):
        return widget.circle.radius >= CircleTool.MIN_RADIUS


def distance((x0, y0), (x1, y1)):
    """Euclidean distance between two points."""
    return hypot(x1-x0, y1-y0)

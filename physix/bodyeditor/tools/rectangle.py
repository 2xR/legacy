from random import random

from physix.bodyeditor.tools.geometry import GeometryTool
from physix.bodyeditor.objects import EditorRectangle


class RectangleTool(GeometryTool):
    MIN_WIDTH = 0.1
    MIN_HEIGHT = 0.1
    button_text = "Rectangle"

    def new_widget(self):
        widget = EditorRectangle()
        widget.hsv = random(), 1, 1
        widget.viewport_size = (1e-9, 1e-9)
        widget.pos = self.init_pos
        return widget

    def update_widget(self, widget):
        width = self.curr_pos[0] - self.init_pos[0]
        height = self.curr_pos[1] - self.init_pos[1]
        # ensure that rectangles have positive width and height,
        # and that the position is correct
        if width < 0:
            widget.x = self.curr_pos[0]
        if height < 0:
            widget.y = self.curr_pos[1]
        widget.viewport_size = (abs(width), abs(height))

    def valid_widget(self, widget):
        return (widget.viewport_width >= RectangleTool.MIN_WIDTH and
                widget.viewport_height >= RectangleTool.MIN_HEIGHT)

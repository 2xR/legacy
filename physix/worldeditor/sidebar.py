from kivyx.widgets import Widget, BoxLayout
from kivyx.links import Link

from kivyx.misc import show_bbox


class Sidebar(Widget):
    def __init__(self, editor):
        Widget.__init__(self)
        self.editor = editor        # Editor
        self._build()

    def _build(self):
        layout = BoxLayout(orientation="vertical")
        show_bbox(layout, color=(0.2, 0.2, 0.2, 0.8))
        Link(layout, size=self, align_xy=self)
        self.add_widget(layout)

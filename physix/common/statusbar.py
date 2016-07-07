from utils.namespace import Namespace

from kivyx.widgets import Widget, Label, BoxLayout
from kivyx.links import Link

from kivyx.misc import show_bbox


class Statusbar(Widget):
    def __init__(self, editor):
        Widget.__init__(self)
        self.editor = editor          # Editor
        self.component = Namespace()  # Namespace(str -> Label)
        self._build()
        self.add_component("changes").size_hint_x = 0.05
        self.add_component("file").size_hint_x = 0.7
        self.add_component("info").size_hint_x = 1.0
        self.add_component("coords").size_hint_x = 0.5

    def _build(self):
        self.layout = BoxLayout(orientation="horizontal")
        show_bbox(self.layout, color=(0.2, 0.2, 0.2, 0.8))
        Link(self.layout, size=self, align_xy=self)
        self.add_widget(self.layout)

    def add_component(self, name, text=""):
        label = Label(font_size="10sp", markup=True)
        self.layout.add_widget(label)
        self.component[name] = label
        return label

    def set_message(self, msg, component="info", italic=True):
        if italic:
            msg = "[i]%s[/i]" % (msg)
        else:
            msg = str(msg)
        self.component[component].text = msg

    def __getitem__(self, comp):
        return self.component[comp]

    def __setitem__(self, comp, msg):
        self.set_message(msg, comp)

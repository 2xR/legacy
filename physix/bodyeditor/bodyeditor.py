from kivyx.widgets import Widget
from kivyx.properties import ObjectProperty
from kivyx.links import Link

from physix.bodyeditor.menubar import MenuBar
from physix.bodyeditor.tools import ToolBar
from physix.bodyeditor.surface import Surface
from physix.bodyeditor.persistence import Persister
from physix.bodyeditor.edithistory import EditHistory
from physix.bodyeditor.filemanager import FileManager
from physix.common import Statusbar

from utils.misc import IDGenerator


class BodyEditor(Widget):
    menubar = ObjectProperty(None)
    toolbar = ObjectProperty(None)
    surface = ObjectProperty(None)
    statusbar = ObjectProperty(None)
    history = ObjectProperty(None)
    persister = ObjectProperty(None)
    file_manager = ObjectProperty(None)

    def __init__(self):
        Widget.__init__(self)
        self.id_generator = IDGenerator()
        self._build()
        self.history = EditHistory(self)
        self.persister = Persister(self)
        self.file_manager = FileManager(self)
        self.toolbar.set_default_tool()

    def _build(self):
        self.menubar = MenuBar(self)
        self.toolbar = ToolBar(self)
        self.statusbar = Statusbar(self)
        self.surface = Surface(self)

        self.add_widget(self.surface)
        self.add_widget(self.menubar)
        self.add_widget(self.toolbar)
        self.add_widget(self.statusbar)

        Link(self.menubar, size=((1.0, 0.05), self),
             align_xy=(Link.TOP, self))
        Link(self.surface, size=((1.0, 0.85), self),
             align_xy=(Link.TOP, self.menubar, Link.BOTTOM))
        Link(self.statusbar, size=((1.0, 0.05), self),
             align_xy=(Link.TOP, self.surface, Link.BOTTOM))
        Link(self.toolbar, size=((1.0, 0.05), self),
             align_xy=(Link.TOP, self.statusbar, Link.BOTTOM))

    def clear(self):
        self.id_generator.count.clear()
        self.surface.clear_objects()
        self.surface.draw_origin()
        self.history.clear()

    reset = clear

    def load(self, filepath):
        self.id_generator.count.clear()
        self.surface.clear_objects()
        self.history.clear()
        self.persister.load(filepath)

    def save(self, filepath):
        self.persister.save(filepath)

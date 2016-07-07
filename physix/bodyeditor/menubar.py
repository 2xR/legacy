from kivyx.widgets import Widget, Button, BoxLayout
from kivyx.links import Link

from physix.bodyeditor.edithistory import EditHistory


class MenuBar(Widget):
    def __init__(self, editor):
        Widget.__init__(self)
        self.editor = editor  # Editor
        self._build()
        if editor.file_manager is not None:
            self._link_to_file_manager(editor, editor.file_manager)
        else:
            editor.bind(file_manager=self._link_to_file_manager)

    def _build(self):
        self.new_btn = Button(text="New")
        self.save_btn = Button(text="Save")
        self.save_as_btn = Button(text="Save as")
        self.load_btn = Button(text="Load")
        self.undo_btn = Button(text="Undo", on_release=self.undo)
        self.redo_btn = Button(text="Redo", on_release=self.redo)

        layout = BoxLayout(orientation="horizontal")
        layout.add_widget(self.new_btn)
        layout.add_widget(self.save_btn)
        layout.add_widget(self.save_as_btn)
        layout.add_widget(self.load_btn)
        layout.add_widget(self.undo_btn)
        layout.add_widget(self.redo_btn)
        Link(layout, size=self, align_xy=self)
        self.add_widget(layout)

    def _link_to_file_manager(self, widget, file_manager):
        self.editor.unbind(file_manager=self._link_to_file_manager)
        self.new_btn.bind(on_release=lambda btn: file_manager.new())
        self.save_btn.bind(on_release=lambda btn: file_manager.save())
        self.save_as_btn.bind(on_release=lambda btn: file_manager.save_as())
        self.load_btn.bind(on_release=lambda btn: file_manager.load())

    def undo(self, widget):
        try:
            self.editor.history.undo()
        except EditHistory.Error as error:
            self.editor.statusbar["info"] = error

    def redo(self, widget):
        try:
            self.editor.history.redo()
        except EditHistory.Error as error:
            self.editor.statusbar["info"] = error

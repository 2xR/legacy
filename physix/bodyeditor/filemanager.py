import os
from functools import partial

from kivyx.widgets import YesNoPopup, FileSelectionPopup, FileSaveAsPopup


class FileManager(object):
    """The file manager keeps track of which file we're currently working on, allowing a "Save"
    button to save to the same file automatically, and a "Save as" to save to another file. Also,
    the file manager keeps track of unsaved changes and prompts for load/new confirmation if the
    current file has unsaved changes.
    The file manager is also responsible for showing the popups for load/save as. The menubar
    should then call the methods on this object."""
    def __init__(self, editor):
        self.editor = editor
        self.filepath = None
        self.unsaved_changes = 0
        self._build()
        self.save_popup.bind(on_okay=self._save)
        self.load_popup.bind(on_okay=self._load)
        if editor.statusbar is not None:
            self._set_filepath(None)
        else:
            editor.bind(statusbar=lambda *args: self._set_filepath(None))

    def _build(self):
        self.discard_popup = YesNoPopup(title="Discard changes to current file?")
        self.discard_popup.auto_dismiss = False
        self.discard_popup.size_hint = (0.5, 0.2)

        self.save_popup = FileSaveAsPopup(title="Save File")
        self.save_popup.filechooser.path = "."
        self.save_popup.default_extension = "json"

        self.load_popup = FileSelectionPopup(title="Load File")
        self.load_popup.filechooser.path = "."
        self.load_popup.default_extension = "json"

    def _set_filepath(self, filepath):
        if filepath is not None:
            self.filepath = os.path.abspath(filepath)
            self.editor.statusbar["file"] = self.filepath
        else:
            self.filepath = None
            self.editor.statusbar["file"] = "<Unsaved File>"
        self.editor.statusbar["changes"] = "---"
        self.unsaved_changes = 0

    def register_change(self, n):
        self.unsaved_changes += n
        self.editor.statusbar["changes"] = "---" if self.unsaved_changes == 0 else "***"

    def _confirm_discard_changes(self, callback):
        cback = partial(self._confirmed_discard_changes, callback=callback)
        cback.keywords["self_ref"] = cback  # ugly hack to allow unbinding below :(
        self.discard_popup.bind(on_yes=cback)
        self.discard_popup.open()

    def _confirmed_discard_changes(self, widget, callback, self_ref):
        self.discard_popup.unbind(on_yes=self_ref)
        callback()

    def new(self, force=False):
        if force or self.unsaved_changes == 0:
            self._set_filepath(None)
            self.editor.clear()
            self.editor.statusbar["info"] = "New file."
        else:
            self._confirm_discard_changes(partial(self.new, force=True))

    def load(self, force=False):
        if force or self.unsaved_changes == 0:
            self.load_popup.open()
        else:
            self._confirm_discard_changes(partial(self.load, force=True))

    def _load(self, widget, directory, files):
        if len(files) == 1:
            self._set_filepath(os.path.join(directory, files[0]))
            self.editor.load(self.filepath)
            self.editor.statusbar["info"] = "File loaded."

    def save(self, force=False):
        if force or self.unsaved_changes != 0:
            if self.filepath is None:
                self.save_as()
            else:
                self._set_filepath(self.filepath)
                self.editor.save(self.filepath)
                self.editor.statusbar["info"] = "File saved."

    def save_as(self):
        self.save_popup.open()

    def _save(self, widget, directory, files):
        if len(files) == 1:
            self._set_filepath(os.path.join(directory, files[0]))
            self.editor.save(self.filepath)
            self.editor.statusbar["info"] = "File saved."
            self.save_popup.filechooser._update_files()
            self.load_popup.filechooser._update_files()

import os

from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView, FileChooserIconView
from kivy.properties import StringProperty, OptionProperty

from kivyx.widgets.yesnopopup import YesNoPopup
from kivyx.links import Link


class FileSelectionPopup(Popup):
    view_type = OptionProperty("list", options=("list", "icons"))
    default_extension = StringProperty("txt")

    def __init__(self, **kwargs):
        Popup.__init__(self, **kwargs)
        self._build()

        self.select_btn.bind(on_release=self.check)
        self.cancel_btn.bind(on_release=self.cancel)
        # NOTE: this is commented out because on_submit doesn't work well
        # self.filechooser.bind(on_submit=self.check)

        self.register_event_type("on_okay")
        self.register_event_type("on_cancel")

    def _build(self):
        self.content = content = Widget()
        self.select_btn = Button(text="Select")
        self.cancel_btn = Button(text="Cancel")
        self.filechooser = (FileChooserListView()
                            if self.view_type == "list" else
                            FileChooserIconView())
        self.filechooser.filters = ["*." + self.default_extension]

        self.buttons = buttons = BoxLayout(orientation="horizontal")
        buttons.add_widget(self.select_btn)
        buttons.add_widget(self.cancel_btn)

        content.add_widget(self.filechooser)
        content.add_widget(buttons)

        Link(self.filechooser, size=((1.0, 0.95), content), align_xy=(Link.TOP, content))
        Link(buttons, size=((1.0, 0.05), content), align_xy=(Link.BOTTOM, content))

    def check(self, *args):
        """This intermediate step is used by FileSaveAsPopup to show a confirmation popup in case
        we're trying to overwrite a file."""
        self.okay()

    def okay(self, *args):
        self.dispatch("on_okay", self.filechooser.path, self.filechooser.selection)

    def cancel(self, *args):
        self.dispatch("on_cancel")

    def on_okay(self, directory, files):
        self.dismiss()

    def on_cancel(self):
        self.dismiss()

    def on_default_extension(self, widget, extension):
        self.filechooser.filters = ["*." + self.default_extension]

    def on_view_type(self, widget, view_type):
        old_filechooser = self.filechooser
        content = self.content
        content.remove_widget(old_filechooser)
        if view_type == "list":
            self.filechooser = FileChooserListView()
        else:
            self.filechooser = FileChooserIconView()
        self.filechooser.path = old_filechooser.path
        self.filechooser.selection = old_filechooser.selection
        self.filechooser.filters = old_filechooser.filters
        self.content.add_widget(self.filechooser)
        Link(self.filechooser, size=((1.0, 0.95), content), align_xy=(Link.TOP, content))


class FileSaveAsPopup(FileSelectionPopup):
    def __init__(self, **kwargs):
        FileSelectionPopup.__init__(self, **kwargs)
        self.file_input.bind(on_text_validate=self.check)
        self.filechooser.bind(selection=self.selection_changed)
        self.overwrite_popup.bind(on_yes=self.okay)

    def _build(self):
        FileSelectionPopup._build(self)
        self.file_input = TextInput(text="New File", multiline=False, focus=True)
        self.overwrite_popup = YesNoPopup(size_hint=(0.5, 0.2), auto_dismiss=False)

        self.content.add_widget(self.file_input)
        Link(self.file_input, size=((1.0, 0.05), self.content),
             align_xy=(Link.BOTTOM, self.buttons, Link.TOP))

    def on_view_type(self, widget, view_type):
        FileSelectionPopup.on_view_type(self, widget, view_type)
        self.filechooser.bind(selection=self.selection_changed)

    def selection_changed(self, widget, selection):
        self.file_input.text = os.path.basename(selection[0])

    def check(self, *args):
        filename = self.file_input.text.strip()
        if len(filename) == 0:
            return
        if not filename.endswith(self.default_extension):
            filename += "." + self.default_extension
            self.filechooser.selection = [filename]
        directory = self.filechooser.path
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            self.overwrite_popup.title = "Overwrite %s?" % (filepath,)
            self.overwrite_popup.open()
        elif os.path.exists(filepath):
            self.cancel()
        else:
            self.okay()

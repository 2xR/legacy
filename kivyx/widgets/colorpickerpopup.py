from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.colorpicker import ColorPicker

from kivyx.links import Link


class ColorPickerPopup(Popup):
    def __init__(self, object, getter, setter, attribute):
        Popup.__init__(self, title="Select Color")
        self.object = object
        self.getter = getter
        self.setter = setter
        self.attribute = attribute
        self._build()

        self.ok_btn.bind(on_release=self.okay)
        self.cancel_btn.bind(on_release=self.cancel)

        self.register_event_type("on_okay")
        self.register_event_type("on_cancel")

    def _build(self):
        self.content = Widget()
        value = self.getter(self.object, self.attribute)
        self.picker = ColorPicker(color=value)
        Link(self.picker, size=((1.0, 0.95), self.content), align_xy=(Link.TOP, self.content))
        self.content.add_widget(self.picker)

        self.ok_btn = Button(text="OK")
        self.cancel_btn = Button(text="Cancel")

        self.buttons = buttons = BoxLayout(orientation="horizontal")
        buttons.add_widget(self.ok_btn)
        buttons.add_widget(self.cancel_btn)
        self.content.add_widget(self.buttons)

        Link(buttons, size=((1.0, 0.05), self.content), align_xy=(Link.BOTTOM, self.content))

    def okay(self, *args):
        self.setter(self.object, self.attribute, self.picker.color)
        self.dispatch("on_okay")

    def cancel(self, *args):
        self.dispatch("on_cancel")

    def on_okay(self):
        self.dismiss()

    def on_cancel(self):
        self.dismiss()

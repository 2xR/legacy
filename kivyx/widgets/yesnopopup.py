from kivyx.widgets import Popup, Button, Widget
from kivyx.links import Link


class YesNoPopup(Popup):
    def __init__(self, **kwargs):
        Popup.__init__(self, **kwargs)
        self._build()
        self.register_event_type("on_yes")
        self.register_event_type("on_no")
        self.yes_btn.bind(on_release=self.yes_pressed)
        self.no_btn.bind(on_release=self.no_pressed)

    def _build(self):
        self.content = Widget()
        self.yes_btn = Button(text="Yes")
        self.no_btn = Button(text="No")
        self.content.add_widget(self.yes_btn)
        self.content.add_widget(self.no_btn)
        Link(self.yes_btn, size=((0.5, 1.0), self.content),
             align_xy=(Link.RIGHT, self.content, Link.CENTER))
        Link(self.no_btn, size=((0.5, 1.0), self.content),
             align_xy=(Link.LEFT, self.content, Link.CENTER))

    def yes_pressed(self, btn):
        self.dispatch("on_yes")

    def no_pressed(self, btn):
        self.dispatch("on_no")

    def on_yes(self):
        self.dismiss()

    def on_no(self):
        self.dismiss()

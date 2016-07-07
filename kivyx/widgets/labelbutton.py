from kivy.uix.label import Label
from kivyx.misc import show_bbox
from kivyx.properties import ListProperty, BooleanProperty, AliasProperty


class LabelButton(Label):
    """A label button class for Kivy, with enable/disable functionality (which kivy's
    button does not offer...).
    The label contains a border which is provided by the always useful show_bbox function."""
    __events__ = ("on_press", "on_release", "on_cancel")

    original_color = ListProperty([1.0, 1.0, 1.0, 1.0])
    pressed_color = ListProperty([0.5, 0.5, 0.5, 1.0])
    disabled_color = ListProperty([0.5, 0.5, 0.5, 0.5])
    pressed = BooleanProperty(False)

    def __init__(self, bgcolor=(0.8, 0.8, 0.8, 0.1), **kwargs):
        self._enabled = True
        Label.__init__(self, **kwargs)
        show_bbox(self, bgcolor, mode="rgba")

    def __get_enabled(self):
        return self._enabled

    def __set_enabled(self, enabled):
        if enabled:
            self.color = self.original_color
        else:
            if self.pressed:
                self.dispatch("on_cancel")
            self.original_color = self.color
            self.color = self.disabled_color
        self._enabled = bool(enabled)

    enabled = AliasProperty(__get_enabled, __set_enabled)

    def on_touch_down(self, touch):
        if self.enabled and not self.pressed and self.collide_point(touch.x, touch.y):
            touch.grab(self)
            self.dispatch("on_press")
            return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if self.enabled:
                if self.collide_point(touch.x, touch.y):
                    self.dispatch("on_release")
                    return True
                else:
                    self.dispatch("on_cancel")

    def on_press(self):
        """Button was pressed."""
        self.original_color = self.color
        self.color = self.pressed_color
        self.pressed = True

    def on_release(self):
        """Touch up received while the touch is over the button."""
        self.color = self.original_color
        self.pressed = False

    def on_cancel(self):
        """Touch up received but the touch is not over the button anymore."""
        self.color = self.original_color
        self.pressed = False

from kivyx.properties import AliasProperty
from kivyx.widgets import Widget


class Clickable(object):
    """A mixin class for adding button behavior to a widget class."""
    events = ("on_press", "on_release", "on_cancel")

    def __init__(self):
        self.__enabled = True
        self.__pressed = False
        for event in Clickable.events:
            self.register_event_type(event)

    def __get_enabled(self):
        return self.__enabled

    def __set_enabled(self, enabled):
        enabled = bool(enabled)
        if not enabled and self.__pressed:
            self.dispatch("on_cancel")
        self.__enabled = enabled

    enabled = AliasProperty(__get_enabled, __set_enabled)

    def __get_pressed(self):
        return self.__pressed

    pressed = AliasProperty(__get_pressed, None)

    def on_touch_down(self, touch):
        if Widget.on_touch_down(self, touch):
            return True
        if self.__enabled and not self.__pressed and self.collide_point(touch.x, touch.y):
            touch.grab(self)
            self.dispatch("on_press")
            return True
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if self.__enabled:
                if self.collide_point(touch.x, touch.y):
                    self.dispatch("on_release")
                    return True
                self.dispatch("on_cancel")
        return False

    def on_press(self):
        """Button was pressed."""
        self.__pressed = True

    def on_release(self):
        """Touch up received while the touch is over the button."""
        self.__pressed = False

    def on_cancel(self):
        """Touch up received but the touch is not over the button anymore."""
        self.__pressed = False

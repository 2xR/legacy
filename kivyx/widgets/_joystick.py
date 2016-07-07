from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.properties import NumericProperty
from kivy.resources import resource_find

from kivyx.links import Link


class Joystick(Widget):
    """An analog joystick widget with two numeric properties representing the x and y axes, with
    values varying from -1 to 1 (0 is neutral)."""
    x_axis = NumericProperty(0.0)
    y_axis = NumericProperty(0.0)

    def __init__(self, **kwargs):
        Widget.__init__(self, **kwargs)
        self.build_layout()

    def build_layout(self):
        self.bg = Image(source=resource_find("joystick_bg.png"),
                        keep_ratio=False, allow_stretch=True)
        self.stick = Image(source=resource_find("joystick_fg.png"),
                           keep_ratio=False, allow_stretch=True)
        self.add_widget(self.bg)
        self.add_widget(self.stick)
        Link(self.bg, size=self, align_xy=self)
        Link(self.stick, size=(0.5, self))
        self.bind(pos=self.reposition_stick, size=self.reposition_stick)

    def reposition_stick(self, *args):
        self.stick.center = (self.center_x + self.x_axis * self.width * 0.5,
                             self.center_y + self.y_axis * self.width * 0.5)

    def set(self, x, y):
        x = min(1.0, max(-1.0, x))
        y = min(1.0, max(-1.0, y))
        self.x_axis = x
        self.y_axis = y
        self.stick.center = (self.center_x + x * self.width * 0.5,
                             self.center_y + y * self.width * 0.5)

    def touched_by(self, touch):
        x = 2.0 * float(touch.x - self.center_x) / self.width
        y = 2.0 * float(touch.y - self.center_y) / self.height
        self.set(x, y)

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            touch.grab(self)
            self.touched_by(touch)
            return True
        return False

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.touched_by(touch)
            return True
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.set(0, 0)
            return True
        return False

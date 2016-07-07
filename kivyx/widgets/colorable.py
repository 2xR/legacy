from kivy.properties import ReferenceListProperty, AliasProperty
from kivy.graphics import Color


class ColorableMixin(object):
    def init(self):
        """This can't be done in __init__() because kivy's stupid authors decided to use super()
        and this class' __init__() would be called out of order, causing attribute error because
        the widget's canvas would not be created yet."""
        with self.canvas.before:
            self.__color = Color(1.0, 1.0, 1.0, 1.0)
            self.__rgba = [1.0, 1.0, 1.0, 1.0]
            self.__hsv = list(self.__color.hsv)

    def rgba_component(index):
        def getter(self):
            return self.__rgba[index]

        def setter(self, x):
            rgba = self.__rgba
            if rgba[index] != x:
                rgba[index] = x
                self.__color.rgba = rgba
                self.trigger_hsv_changes()
                return True
            return False
        return AliasProperty(getter, setter)

    def hsv_component(index):
        def getter(self):
            return self.__hsv[index]

        def setter(self, x):
            hsv = self.__hsv
            if hsv[index] != x:
                hsv[index] = x
                self.__color.hsv = hsv
                self.__color.a = self.__rgba[-1]
                self.trigger_rgba_changes()
                return True
            return False
        return AliasProperty(getter, setter)

    def trigger_rgba_changes(self):
        cls = type(self)
        self_rgba = self.__rgba
        color_rgba = self.__color.rgba
        for index, component in enumerate("rgba"):
            prop_value = self_rgba[index]
            color_value = color_rgba[index]
            if prop_value != color_value:
                self_rgba[index] = color_value
                getattr(cls, component).trigger_change(self, color_value)

    def trigger_hsv_changes(self):
        cls = type(self)
        self_hsv = self.__hsv
        color_hsv = self.__color.hsv
        for index, component in enumerate("hsv"):
            prop_value = self_hsv[index]
            color_value = color_hsv[index]
            if prop_value != color_value:
                self_hsv[index] = color_value
                getattr(cls, component).trigger_change(self, color_value)

    def get_hsv(self):
        return list(self.__hsv)

    def set_hsv(self, hsv):
        """This is a special case because in some situations using a ReferenceListProperty would
        cause the value of hsv to be lost because its components would be set one at a time. This
        way we set all three components of hsv at once, and keep the alpha channel (kivy discards
        alpha when setting hsv on a Color instruction)."""
        self.__color.hsv = hsv
        self.__color.a = self.__rgba[-1]
        self.trigger_hsv_changes()
        self.trigger_rgba_changes()

    r = rgba_component(0)
    g = rgba_component(1)
    b = rgba_component(2)
    a = rgba_component(3)
    h = hsv_component(0)
    s = hsv_component(1)
    v = hsv_component(2)
    rgb = ReferenceListProperty(r, g, b)
    rgba = ReferenceListProperty(r, g, b, a)
    hsv = AliasProperty(get_hsv, set_hsv, bind=("h", "s", "v"))

    del rgba_component
    del hsv_component
    del get_hsv
    del set_hsv

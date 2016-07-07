from functools import partial

from kivyx.widgets import (Spinner, CheckBox, BoxLayout, TextInput, ImageButton, Widget,
                           Label, Button, Popup)
from kivyx.links import Link
from kivyx.resources import resource_find
from kivyx.lib import Clock

from physix.bodyeditor.edithistory import ChangeSettings


def get_custom(obj, attr):
    try:
        return obj.custom_settings[attr]
    except KeyError:
        return None


def set_custom(obj, attr, value):
    obj.custom_settings[attr] = value


class Setting(object):
    def __init__(self, name, default, attr=None, getter=getattr, setter=setattr):
        if attr is None:
            attr = name.lower()
        self.getter = getter
        self.setter = setter
        self.name = name
        self.default = default
        self.attr = attr

    def get_from_widget(self, widget):
        raise NotImplementedError()

    def build(self, obj):
        """Build a widget for configuring the argument object. Initial values of subwidgets like
        sliders or spinners should use the current settings of the object."""
        raise NotImplementedError()


class TextSetting(Setting):
    def __init__(self, name, default=None, attr=None, getter=getattr, setter=setattr):
        Setting.__init__(self, name, default, attr, getter, setter)

    @staticmethod
    def add_custom_to_object(name, attr, custom_widget, obj):
        if name is None or not name.strip():
            return False
        if attr is None or not attr.strip():
            return False
        if attr in obj.custom_settings:
            return False

        default = custom_widget.text_input.text.strip()
        obj.settings.append(TextSetting(name=name.strip(), default=default,
                            attr=attr.strip(), getter=get_custom, setter=set_custom))
        set_custom(obj, attr, default)
        return True

    def build(self, obj):
        value = self.getter(obj, self.attr)
        return TextInput(text=str(value), multiline=False)

    def get_from_widget(self, widget):
        return widget.text

    @staticmethod
    def build_custom_widget():
        layout = BoxLayout(orientation="horizontal")
        layout.add_widget(Label(text="Default Value", font_size="12sp"))
        layout.text_input = TextInput(text="Default", multiline=False)
        layout.add_widget(layout.text_input)
        layout.gravity = 1
        return layout


class OptionSetting(Setting):
    def __init__(self, name, options, default=None, attr=None, getter=getattr, setter=setattr):
        options = list(options)
        if default is None:
            default = options[0]
        Setting.__init__(self, name, default, attr, getter, setter)
        self.options = options

    @staticmethod
    def add_custom_to_object(name, attr, custom_widget, obj):
        if name is None or not name.strip():
            return False
        if attr is None or not attr.strip():
            return False
        if attr in obj.custom_settings:
            return False

        default = custom_widget.text_input.text.strip()
        size = len(custom_widget).items
        if size == 0 or (size == 1 and default in custom_widget.items):
            return False
        if default not in custom_widget.items:
            custom_widget.items.append(default)
        obj.settings.append(OptionSetting(name=name.strip(), options=custom_widget.items,
                            default=default, attr=attr.strip(), getter=get_custom,
                            setter=set_custom))
        set_custom(obj, attr, default)
        return True

    def build(self, obj):
        return Spinner(text=self.getter(obj, self.attr), font_size="12sp", values=self.options)

    def get_from_widget(self, widget):
        return widget.text

    @staticmethod
    def build_custom_widget():
        v_layout = BoxLayout(orientation="vertical")
        v_layout.items = []

        layout = BoxLayout(orientation="horizontal")
        layout.add_widget(Label(text="Default Value", font_size="12sp"))
        v_layout.text_input = TextInput(text="Text", multiline=False)
        layout.add_widget(v_layout.text_input)
        v_layout.add_widget(layout)
        layout = BoxLayout(orientation="horizontal")
        layout.add_widget(Label(text="Other Options", font_size="12sp"))
        vertical = BoxLayout(orientation="vertical")
        inner = BoxLayout(orientation="horizontal")
        text = TextInput(text="", multiline=False)
        inner.add_widget(text)
        button = Button(text="Add New")
        button.bind(on_release=partial(OptionSetting.custom_add_item, v_layout, text, vertical))
        inner.add_widget(button)
        vertical.add_widget(inner)
        layout.add_widget(vertical)
        v_layout.add_widget(layout)
        v_layout.gravity = 2
        return v_layout

    @staticmethod
    def custom_add_item(custom_widget, text_input, layout, button):
        if text_input.text is None or not text_input.text.strip():
            return
        new_item = text_input.text.strip()
        custom_widget.items.append(new_item)
        text_input.text = ""
        inner = BoxLayout(orientation="horizontal")
        inner.add_widget(Label(text=new_item, font_size="12sp"))
        button = Button(text="Remove")
        button.bind(on_release=partial(OptionSetting.custom_remove_item, custom_widget,
                    new_item, layout, inner))
        inner.add_widget(button)
        layout.add_widget(inner)
        custom_widget.gravity += 1
        getattr(custom_widget, "__link").destroy()
        Link(custom_widget, size=((1.0, custom_widget.gravity * 0.05), custom_widget.parent),
             align_xy=(Link.TOP, custom_widget.parent.custom_anchor, Link.BOTTOM))

    @staticmethod
    def custom_remove_item(custom_widget, item, layout, widget, button):
        custom_widget.items.remove(item)
        layout.remove_widget(widget)
        custom_widget.gravity -= 1
        getattr(custom_widget, "__link").destroy()
        Link(custom_widget, size=((1.0, custom_widget.gravity * 0.05), custom_widget.parent),
             align_xy=(Link.TOP, custom_widget.parent.custom_anchor, Link.BOTTOM))


class BooleanSetting(OptionSetting):
    def __init__(self, name, default=True, attr=None, getter=getattr, setter=setattr):
        OptionSetting.__init__(self, name, [False, True], default, attr, getter, setter)

    @staticmethod
    def add_custom_to_object(name, attr, custom_widget, obj):
        if name is None or not name.strip():
            return False
        if attr is None or not attr.strip():
            return False
        if attr in obj.custom_settings:
            return False
        default = custom_widget.checkbox.active
        obj.settings.append(BooleanSetting(name=name.strip(), default=default,
                            attr=attr.strip(), getter=get_custom, setter=set_custom))
        set_custom(obj, attr, default)
        return True

    def build(self, obj):
        return CheckBox(active=self.getter(obj, self.attr))

    def get_from_widget(self, widget):
        return bool(widget.active)

    @staticmethod
    def build_custom_widget():
        layout = BoxLayout(orientation="horizontal")
        layout.add_widget(Label(text="Default Value", font_size="12sp"))
        layout.checkbox = CheckBox(active=True)
        layout.add_widget(layout.checkbox)
        layout.gravity = 1
        return layout


class NumericSetting(Setting):
    def __init__(self, name, min=None, max=None, step=0.01, default=None, attr=None,
                 getter=getattr, setter=setattr):
        if default is None:
            if min is None and max is None:
                default = 0.0
            elif min is None:
                default = max
            else:
                default = min
        Setting.__init__(self, name, default, attr, getter, setter)
        self.min = min
        self.max = max
        self.step = step

    @staticmethod
    def add_custom_to_object(name, attr, custom_widget, obj):
        if name is None or not name.strip():
            return False
        if attr is None or not attr.strip():
            return False
        if attr in obj.custom_settings:
            return False
        default = custom_widget.default.text.strip()
        try:
            default = int(default)
        except ValueError:
            try:
                default = float(default)
            except ValueError:
                return False

        minimum = custom_widget.minimum.text.strip()
        try:
            minimum = int(minimum)
        except ValueError:
            try:
                minimum = float(minimum)
            except ValueError:
                return False

        maximum = custom_widget.maximum.text.strip()
        try:
            maximum = int(maximum)
        except ValueError:
            try:
                maximum = float(maximum)
            except ValueError:
                return False

        step = custom_widget.step.text.strip()
        try:
            step = int(step)
        except ValueError:
            try:
                step = float(step)
            except ValueError:
                return False

        if minimum > maximum:
            return False
        if default < minimum or default > maximum:
            return False

        obj.settings.append(NumericSetting(name=name.strip(), default=default,
                            min=minimum, max=maximum, step=step, attr=attr.strip(),
                            getter=get_custom, setter=set_custom))
        set_custom(obj, attr, default)
        return True

    @staticmethod
    def build_custom_widget():
        v_layout = BoxLayout(orientation="vertical")
        layout = BoxLayout(orientation="horizontal")
        layout.add_widget(Label(text="Default Value", font_size="12sp"))
        inner = BoxLayout(orientation="horizontal")
        text_input, increase, decrease = NumericSetting.build_trio(0)
        text_input.bind(on_text_validate=NumericSetting.custom_check_number)
        increase.bind(on_press=NumericSetting.custom_button_pressed,
                      on_release=NumericSetting.custom_button_released,
                      on_cancel=NumericSetting.custom_button_released)
        decrease.bind(on_press=NumericSetting.custom_button_pressed,
                      on_release=NumericSetting.custom_button_released,
                      on_cancel=NumericSetting.custom_button_released)
        v_layout.default = text_input
        inner.add_widget(decrease)
        inner.add_widget(text_input)
        inner.add_widget(increase)
        layout.add_widget(inner)
        v_layout.add_widget(layout)

        layout = BoxLayout(orientation="horizontal")
        layout.add_widget(Label(text="Minimum Value", font_size="12sp"))
        inner = BoxLayout(orientation="horizontal")
        text_input, increase, decrease = NumericSetting.build_trio(0)
        text_input.bind(on_text_validate=NumericSetting.custom_check_number)
        increase.bind(on_press=NumericSetting.custom_button_pressed,
                      on_release=NumericSetting.custom_button_released,
                      on_cancel=NumericSetting.custom_button_released)
        decrease.bind(on_press=NumericSetting.custom_button_pressed,
                      on_release=NumericSetting.custom_button_released,
                      on_cancel=NumericSetting.custom_button_released)
        v_layout.minimum = text_input
        inner.add_widget(decrease)
        inner.add_widget(text_input)
        inner.add_widget(increase)
        layout.add_widget(inner)
        v_layout.add_widget(layout)

        layout = BoxLayout(orientation="horizontal")
        layout.add_widget(Label(text="Maximum Value", font_size="12sp"))
        inner = BoxLayout(orientation="horizontal")
        text_input, increase, decrease = NumericSetting.build_trio(0)
        text_input.bind(on_text_validate=NumericSetting.custom_check_number)
        increase.bind(on_press=NumericSetting.custom_button_pressed,
                      on_release=NumericSetting.custom_button_released,
                      on_cancel=NumericSetting.custom_button_released)
        decrease.bind(on_press=NumericSetting.custom_button_pressed,
                      on_release=NumericSetting.custom_button_released,
                      on_cancel=NumericSetting.custom_button_released)
        v_layout.maximum = text_input
        inner.add_widget(decrease)
        inner.add_widget(text_input)
        inner.add_widget(increase)
        layout.add_widget(inner)
        v_layout.add_widget(layout)

        layout = BoxLayout(orientation="horizontal")
        layout.add_widget(Label(text="Step Value", font_size="12sp"))
        inner = BoxLayout(orientation="horizontal")
        text_input, increase, decrease = NumericSetting.build_trio(0.03)
        text_input.bind(on_text_validate=NumericSetting.custom_check_number)
        increase.bind(on_press=NumericSetting.custom_button_pressed,
                      on_release=NumericSetting.custom_button_released,
                      on_cancel=NumericSetting.custom_button_released)
        decrease.bind(on_press=NumericSetting.custom_button_pressed,
                      on_release=NumericSetting.custom_button_released,
                      on_cancel=NumericSetting.custom_button_released)
        v_layout.step = text_input
        inner.add_widget(decrease)
        inner.add_widget(text_input)
        inner.add_widget(increase)
        layout.add_widget(inner)
        v_layout.add_widget(layout)

        v_layout.gravity = 4
        return v_layout

    @staticmethod
    def custom_check_number(text_input):
        try:
            value = int(text_input.text)
        except ValueError:
            try:
                value = float(text_input.text)
            except ValueError:
                value = text_input.value
        text_input.text = str(value)
        text_input.value = value

    @staticmethod
    def custom_button_pressed(button):
        button.speed = 0.0
        button.callback = partial(NumericSetting.custom_change, button)
        NumericSetting.custom_change(button, 0.0)
        Clock.schedule_interval(button.callback, 0.25)

    @staticmethod
    def custom_button_released(button):
        Clock.unschedule(button.callback)

    @staticmethod
    def custom_change(button, dt):
        button.speed += 0.05 * button.sign
        value = button.text_input.value + button.speed
        button.text_input.value = value
        button.text_input.text = str(value)

    @staticmethod
    def build_trio(value):
        text_input = TextInput(text=str(value), multiline=False)
        text_input.value = value

        increase = ImageButton(source=resource_find("increase.png"),
                               keep_ratio=True, allow_stretch=True)
        increase.text_input = text_input
        increase.sign = +1.0

        decrease = ImageButton(source=resource_find("decrease.png"),
                               keep_ratio=True, allow_stretch=True)
        decrease.text_input = text_input
        decrease.sign = -1.0

        return text_input, increase, decrease

    def build(self, obj):
        init_value = self.getter(obj, self.attr)
        text_input, increase, decrease = NumericSetting.build_trio(init_value)
        text_input.bind(on_text_validate=self.check_number)
        increase.bind(on_press=self.button_pressed,
                      on_release=self.button_released,
                      on_cancel=self.button_released)
        decrease.bind(on_press=self.button_pressed,
                      on_release=self.button_released,
                      on_cancel=self.button_released)

        box_layout = BoxLayout(orientation="horizontal")
        box_layout.add_widget(decrease)
        box_layout.add_widget(text_input)
        box_layout.add_widget(increase)
        box_layout.text_input = text_input
        return box_layout

    def button_pressed(self, button):
        button.speed = 0.0
        button.callback = partial(self.change, button)
        self.change(button, 0.0)
        Clock.schedule_interval(button.callback, 0.25)

    def button_released(self, button):
        Clock.unschedule(button.callback)

    def change(self, button, dt):
        button.speed += self.step * button.sign
        value = button.text_input.value + button.speed
        if self.min is not None:
            value = max(value, self.min)
        if self.max is not None:
            value = min(value, self.max)
        button.text_input.value = value
        button.text_input.text = str(value)

    def check_number(self, text_input):
        try:
            value = float(text_input.text)
        except ValueError:
            text_input.text = str(text_input.value)
        else:
            if self.min is not None:
                value = max(value, self.min)
            if self.max is not None:
                value = min(value, self.max)
            text_input.value = value
            text_input.text = str(value)

    def get_from_widget(self, widget):
        return widget.text_input.value


class SettingsPopup(Popup):
    def __init__(self, obj, editor, **kwargs):
        Popup.__init__(self, title="Physics Settings", **kwargs)
        self.object = obj
        self.editor = editor
        self._build()

        self.ok_btn.bind(on_release=self.okay)
        self.cancel_btn.bind(on_release=self.cancel)
        self.custom_btn.bind(on_release=self.add_custom_setting)

        self.register_event_type("on_okay")
        self.register_event_type("on_cancel")

    def add_custom_setting(self, *args):
        CustomSettingsPopup(self.object).open()
        self.okay()

    def _build(self):
        self.content = Widget()
        self.created_widgets = []
        v_layout = BoxLayout(orientation="vertical")
        for setting in self.object.settings:
            h_layout = BoxLayout(orientation="horizontal")
            label = Label(text=setting.name, font_size="12sp")
            h_layout.add_widget(label)

            widget = setting.build(self.object)
            self.created_widgets.append(widget)
            h_layout.add_widget(widget)
            v_layout.add_widget(h_layout)

        self.content.add_widget(v_layout)
        rel_height = 0.05 * len(type(self.object).settings)
        Link(v_layout, size=((1.0, rel_height), self.content), align_xy=(Link.TOP, self.content))

        self.custom_btn = Button(text="Add Custom Setting")
        self.ok_btn = Button(text="OK")
        self.cancel_btn = Button(text="Cancel")

        self.buttons = buttons = BoxLayout(orientation="horizontal")
        buttons.add_widget(self.custom_btn)
        buttons.add_widget(self.ok_btn)
        buttons.add_widget(self.cancel_btn)
        self.content.add_widget(self.buttons)

        Link(buttons, size=((1.0, 0.05), self.content), align_xy=(Link.BOTTOM, self.content))

    def okay(self, *args):
        old_settings = {}
        for setting in type(self.object).settings:
            old_settings[setting.attr] = setting.getter(self.object, setting.attr)

        new_settings = {}
        setters = {}
        for setting, widget in zip(type(self.object).settings, self.created_widgets):
            new_settings[setting.attr] = setting.get_from_widget(widget)
            setters[setting.attr] = setting.setter

        if new_settings != old_settings:
            command = ChangeSettings(self.object, old_settings, new_settings, setters)
            self.editor.history.append(command)
            self.dispatch("on_okay")
        else:
            self.dispatch("on_cancel")

    def cancel(self, *args):
        self.dispatch("on_cancel")

    def on_okay(self):
        self.dismiss()

    def on_cancel(self):
        self.dismiss()


class CustomSettingsPopup(Popup):
    def __init__(self, obj, **kwargs):
        Popup.__init__(self, title="Custom Settings", **kwargs)
        self.object = obj
        self._build()

        self.ok_btn.bind(on_release=self.okay)
        self.cancel_btn.bind(on_release=self.cancel)

        self.register_event_type("on_okay")
        self.register_event_type("on_cancel")

    def _build(self):
        self.content = Widget()

        v_layout = BoxLayout(orientation="vertical")
        # setting name
        h_layout = BoxLayout(orientation="horizontal")
        label = Label(text="Setting Name", font_size="12sp")
        h_layout.add_widget(label)
        self.name = TextInput(text="Custom", multiline=False)
        h_layout.add_widget(self.name)
        v_layout.add_widget(h_layout)
        # attribute name
        h_layout = BoxLayout(orientation="horizontal")
        label = Label(text="Attribute Name", font_size="12sp")
        h_layout.add_widget(label)
        self.attr = TextInput(text="custom", multiline=False)
        h_layout.add_widget(self.attr)
        v_layout.add_widget(h_layout)
        # setting type
        h_layout = BoxLayout(orientation="horizontal")
        label = Label(text="Setting Type", font_size="12sp")
        h_layout.add_widget(label)
        text = Spinner(text="TextSetting", font_size="12sp", values=["TextSetting",
                       "BooleanSetting", "OptionSetting", "NumericSetting"])
        text.bind(text=self._change_setting_type)
        h_layout.add_widget(text)
        v_layout.add_widget(h_layout)

        self.content.add_widget(v_layout)
        Link(v_layout, size=((1.0, 3.0 * 0.05), self.content), align_xy=(Link.TOP, self.content))

        # setting type custom
        self.content.custom_anchor = v_layout
        self.custom_widget = TextSetting.build_custom_widget()
        self.custom_widget.setting_class = TextSetting
        self.content.add_widget(self.custom_widget)
        Link(self.custom_widget, size=((1.0, self.custom_widget.gravity * 0.05), self.content),
             align_xy=(Link.TOP, self.content.custom_anchor, Link.BOTTOM))

        self.ok_btn = Button(text="OK")
        self.cancel_btn = Button(text="Cancel")

        self.buttons = buttons = BoxLayout(orientation="horizontal")
        buttons.add_widget(self.ok_btn)
        buttons.add_widget(self.cancel_btn)
        self.content.add_widget(self.buttons)

        Link(buttons, size=((1.0, 0.05), self.content), align_xy=(Link.BOTTOM, self.content))

    def _change_setting_type(self, spinner, text):
        self.content.remove_widget(self.custom_widget)
        getattr(self.custom_widget, "__link").destroy()
        self.custom_widget = globals()[text].build_custom_widget()
        self.custom_widget.setting_class = globals()[text]
        self.content.add_widget(self.custom_widget)
        Link(self.custom_widget, size=((1.0, self.custom_widget.gravity * 0.05), self.content),
             align_xy=(Link.TOP, self.content.custom_anchor, Link.BOTTOM))

    def okay(self, *args):
        cls = self.custom_widget.setting_class
        if cls.add_custom_to_object(self.name.text, self.attr.text,
                                    self.custom_widget, self.object):
            self.dispatch("on_okay")

    def cancel(self, *args):
        self.dispatch("on_cancel")

    def on_okay(self):
        self.dismiss()

    def on_cancel(self):
        self.dismiss()

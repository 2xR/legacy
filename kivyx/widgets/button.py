from kivyx.widgets.clickable import Clickable
from kivy.uix.button import Button as KivyButton


class Button(Clickable, KivyButton):
    def __init__(self, **kwargs):
        KivyButton.__init__(self, **kwargs)
        Clickable.__init__(self)

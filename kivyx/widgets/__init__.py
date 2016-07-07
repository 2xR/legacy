# Kivy "native" widgets
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.image import Image, AsyncImage
from kivy.uix.button import Button
from kivy.uix.scatter import Scatter, ScatterPlane
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserIconView, FileChooserListView
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.progressbar import ProgressBar

# Kivyx widgets
from kivyx.widgets.ellipse import Ellipse
from kivyx.widgets.circle import Circle
from kivyx.widgets.rectangle import Rectangle
from kivyx.widgets.transform import Transform
from kivyx.widgets.stencil import Stencil
from kivyx.widgets.imagebutton import ImageButton
from kivyx.widgets.yesnopopup import YesNoPopup
from kivyx.widgets.fileselectionpopup import FileSelectionPopup, FileSaveAsPopup
from kivyx.widgets.colorpickerpopup import ColorPickerPopup
from kivyx.widgets.labelbutton import LabelButton
from kivyx.widgets.camera import Camera

# Kivyx widget utility classes
from kivyx.widgets.colorable import ColorableMixin

# from kivyx.widgets.button import Button
# from kivyx.widgets.sprite import Sprite
# from kivyx.widgets.joystick import Joystick
# from kivyx.widgets.clickable import Clickable

kivy_widgets = [Widget, Label, Image, AsyncImage, Button, Scatter, ScatterPlane,
                BoxLayout, Popup, Slider, Spinner, CheckBox, TextInput,
                FileChooserIconView, FileChooserListView, ColorPicker, ProgressBar]
kivyx_widgets = [Ellipse, Circle, Rectangle, Transform, Stencil, ImageButton,
                 YesNoPopup, FileSelectionPopup, FileSaveAsPopup, ColorPickerPopup,
                 LabelButton, Camera]
kivyx_mixins = [ColorableMixin]


from utils import attr
from itertools import chain

__all__ = map(attr.getter("__name__"), chain(kivy_widgets, kivyx_widgets, kivyx_mixins))

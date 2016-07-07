from utils.prettyrepr import prettify_class
from kivyx.widgets import Rectangle

from physix.common import EditorObject
from physix.common.physics import DENSITY, FRICTION, RESTITUTION, SENSOR


@prettify_class
@EditorObject.register_class
class EditorRectangle(EditorObject):
    __info_attrs__ = ("pos", "size")

    registry_key = "rectangle"
    spec_attrs = EditorObject.spec_attrs + ("viewport_size", "rotation", "center",
                                            "rgba", "physics")

    settings = EditorObject.settings + [DENSITY, FRICTION, RESTITUTION, SENSOR]

    def __init__(self):
        EditorObject.__init__(self)
        self.rectangle = Rectangle()
        self.add_widget(self.rectangle)
        self.bind(viewport_size=self.rectangle.setter("size"),
                  viewport_pos=self.rectangle.setter("pos"),
                  rgba=self.rectangle.setter("rgba"))

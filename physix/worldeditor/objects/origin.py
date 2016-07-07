from physix.common import EditorObject
from physix.common.physics import DO_SLEEP, H_GRAVITY, V_GRAVITY


@EditorObject.register_class
class Origin(EditorObject):
    registry_key = "origin"
    spec_attrs = ("pos", "physics")

    physics_settings = [DO_SLEEP, H_GRAVITY, V_GRAVITY]

    resizable = False
    rotatable = False
    deletable = False
    clonable = False

    def __init__(self):
        EditorObject.__init__(self)
        self.unbind(viewport_size=self.center_viewport_on_origin)
        self.viewport_size = (1.0, 1.0)
        self.debug_origin = True

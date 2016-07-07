from physix.common import EditorObject
from physix.common.physics import (LINEAR_DAMPING, ANGULAR_DAMPING, GRAVITY_SCALE, AWAKE, ACTIVE,
                                   ALLOW_SLEEP, FIXED_ROTATION, BULLET, BODY_TYPE)


@EditorObject.register_class
class Origin(EditorObject):
    registry_key = "origin"
    spec_attrs = EditorObject.spec_attrs + ("pos", "physics")

    settings = EditorObject.settings + [LINEAR_DAMPING, ANGULAR_DAMPING, GRAVITY_SCALE,
                                        ALLOW_SLEEP, AWAKE, FIXED_ROTATION, BULLET,
                                        ACTIVE, BODY_TYPE]

    resizable = False
    rotatable = False
    deletable = False
    clonable = False

    def __init__(self):
        EditorObject.__init__(self)
        self.unbind(viewport_size=self.center_viewport_on_origin)
        self.viewport_size = (1.0, 1.0)
        self.debug_origin = True

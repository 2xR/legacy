from copy import deepcopy
from utils.misc import check_type
from kivyx.widgets import Transform, ColorableMixin

from physix.common.physics import IDENTIFIER


class EditorObject(Transform, ColorableMixin):
    """Base class for all editor objects. Subclasses should define a 'spec_attrs' class attribute
    (an iterable containing strings) listing which object attributes constitue its spec. This class
    provides a default extractor and constructor based on the 'spec_attrs' list, but subclasses may
    define more complex behavior if desired, by redefining extract_spec() (a bound method) and
    from_spec() (a class method).
    """
    registry = {}  # {str: EditorObject type}
    registry_key = "object"
    spec_attrs = ("id", "custom_settings")
    settings = [IDENTIFIER]

    movable = True
    resizable = True
    rotatable = True
    deletable = True
    clonable = True

    def __init__(self):
        Transform.__init__(self)
        ColorableMixin.init(self)
        self.bind(viewport_size=self.center_viewport_on_origin)
        self.physics = {}
        self.custom_settings = {}
        self.init_settings()

    def init_settings(self):
        for setting in type(self).settings:
            setting.setter(self, setting.attr, setting.default)

    def center_viewport_on_origin(self, *args):
        self.viewport_center = (0, 0)

    def duplicate(self):
        spec = deepcopy(self.extract_spec())
        spec["data"]["id"] = None  # force generation of a new id for the clone
        return type(self).from_spec(spec)

    def extract_spec(self):
        """extract_spec() -> spec (dict)
        Extract a spec, i.e. a set of attributes which entirely define the object. The spec must be
        a dictionary, and must have a 'type' key indicating which type from the object registry
        should be used when loading the object (using from_spec())."""
        cls = type(self)
        data = {attr: getattr(self, attr) for attr in cls.spec_attrs}
        return {"type": cls.registry_key, "data": data}

    @classmethod
    def from_spec(cls, spec):
        """from_spec(spec) -> EditorObject
        Construct an editor object from a spec extracted earlier."""
        if spec["type"] != cls.registry_key:
            raise TypeError("mismatching registry key: %s does not correspond to %s" %
                            (cls.registry_key, spec))
        data = spec["data"]
        if set(data.iterkeys()) != set(cls.spec_attrs):
            raise ValueError("invalid %s spec: %s" % (spec["type"], spec))
        # IMPORTANT: set attrs using the order in cls.spec_attrs! If we reposition the widget
        # and then resize it we may (and probably will) get different results. Always remember
        # to resize before repositioning! This is done by simply putting any size attributes
        # before position attributes in 'spec_attrs'.
        self = cls()
        for attr in cls.spec_attrs:
            setattr(self, attr, data[attr])
        return self

    @staticmethod
    def register_class(cls):
        """Class decorator used to add an editor object class to the class registry."""
        try:
            key = cls.__dict__["registry_key"]
        except KeyError:
            raise KeyError("editor object type must define a registry key")
        check_type(key, str)
        if key in EditorObject.registry:
            raise KeyError("conflicting registry key %r" % (key,))
        EditorObject.registry[key] = cls
        return cls

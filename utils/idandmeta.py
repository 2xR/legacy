from utils.misc import IDGenerator
from utils.namespace import Namespace
from utils.prettyrepr import prettify_class
from utils.copy import fetch_copy


@prettify_class
class IdAndMeta(object):
    """An object with an 'id' attribute and a namespace holding metadata concerning the object."""
    id_generator = IDGenerator()

    __slots__ = ("id", "meta")

    def __init__(self, id=None, **meta):
        self.id = id if id is not None else IdAndMeta.id_generator.generate(self)
        self.meta = Namespace(meta)

    def __info__(self):
        return self.id

    def __deepcopy__(self, memo):
        clone = fetch_copy(self, memo)
        clone.id = self.id
        clone.meta = Namespace(self.meta)
        return clone

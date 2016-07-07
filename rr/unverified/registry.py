from utils.multiset import MultiSet


class Registry(dict):
    """This object is responsible for keeping track of objects and assigning unique identifiers to
    all of them, ensuring that the same object has the same ID even on different machines (server
    and clients for instance). If an object already has an id assigned at the time of insertion
    into the registry, the registry will use that identifier provided it is not being used by
    another object (in which case a ValueError will be raised)."""
    def __init__(self, id_attribute="id"):
        dict.__init__(self)
        self.count = MultiSet()
        self.id_attribute = id_attribute

    def __contains__(self, obj):
        """If passed a string, uses normal dictionary lookup, otherwise it looks up the argument's
        id and matches the registered object with the argument."""
        if isinstance(obj, str):
            return dict.__contains__(self, obj)
        try:
            id = self.get_identifier(obj)
        except AttributeError:
            return False
        try:
            return obj is self[id]
        except KeyError:
            return False

    def add(self, obj):
        try:
            id = self.get_identifier(obj)
        except AttributeError:
            cls = type(obj)
            count = self.count.insert(cls) - 1
            id = "%s#%s" % (cls.__name__, count)
            setattr(obj, self.id_attribute, id)
        else:
            if id in self:
                raise ValueError("duplicate id in registry object - %r" % id)
        self[id] = obj

    def remove(self, obj):
        id = self.get_identifier(obj)
        if self[id] is not obj:
            raise ValueError("object mismatch")
        delattr(obj, self.id_attribute)
        del self[id]

    def discard(self, obj):
        if obj in self:
            self.remove(obj)

    def get_identifier(self, obj):
        return getattr(obj, self.id_attribute)

    def set_identifier(self, obj, id):
        if obj in self:
            if id in self:
                raise Exception("cannot set identifier (already in use)")
            del self[self.get_identifier(obj)]
            self[id] = obj
        setattr(obj, self.id_attribute, id)



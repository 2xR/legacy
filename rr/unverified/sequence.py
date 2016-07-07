class SequenceLike(object):
    """This mixin class provides default magic methods (__getitem__, __setitem__, __delitem__,
    __len__, __iter__, and __contains__) for a subclass to emulate a sequence type, mapping the
    attributes listed in the '__items__' class attribute to positions in a virtual sequence. The
    default __len__ magic method always returns the size of __items__, but subclasses may want to
    redefine this behavior.
    This class provides simple iteration, item get/set/del, membership testing, and len."""
    __slots__ = ()
    __items__ = ()

    def __getitem__(self, i):
        return getattr(self, type(self).__items__[i])

    def __setitem__(self, i, v):
        setattr(self, type(self).__items__[i], v)

    def __delitem__(self, i):
        delattr(self, type(self).__items__[i])

    def __len__(self):
        return len(type(self).__items__)

    def __iter__(self):
        for item in type(self).__items__:
            yield getattr(self, item)

    def __contains__(self, v):
        return any(v == x for x in self)

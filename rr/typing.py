def ensure_type(obj, cls, none_allowed=False):
    """A simple type-checking function that raises a TypeError if 'obj' is not as instance of
    'cls'. The second argument, 'cls', may be a type or a tuple of classes, like the argument to
    isinstance(). If 'none_allowed' is true, no error is raised if 'obj' is None."""
    if none_allowed and obj is None or isinstance(obj, cls):
        return True
    raise not_instance(obj, cls, none_allowed)


def not_instance(obj, cls, none_allowed=False):
    """Creates a TypeError instance with a helpful description of the error."""
    if isinstance(cls, tuple):
        cls_name = "one of {" + ", ".join(c.__name__ for c in cls) + "}"
    else:
        cls_name = cls.__name__
    if none_allowed:
        cls_name += " (or None)"
    return TypeError("expected instance of {}, got {} instead".format(cls_name, type(obj).__name__))


def ensure_subclass(cls, super_cls):
    """Similar to ensure_type(), but for checking if a class is a subclass of another."""
    if issubclass(cls, super_cls):
        return True
    raise not_subclass(cls, super_cls)


def not_subclass(cls, super_cls):
    """Creates a TypeError instance with a helpful description of the error."""
    if isinstance(super_cls, tuple):
        super_cls_name = "one of {" + ", ".join(c.__name__ for c in super_cls) + "}"
    else:
        super_cls_name = super_cls.__name__
    return TypeError("expected subclass of {}, got {} instead".format(super_cls_name, cls.__name__))

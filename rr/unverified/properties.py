from functools import partial
from itertools import izip

from utils.misc import check_type
from utils.call import MultiCall


class CustomProperty(property):
    """A property subclass that supports multiple callbacks on retrieval, assignment and deletion.
    These callbacks are free to do anything, but they may be especially useful for things such as
    bounds or type checks, or restricting the property's value to a certain domain (e.g. to create
    an enum property).

    Callbacks should raise their own exceptions if the requested operation is invalid for some
    reason. The return value of a callback function is ignored by the property, so the callback is
    free to return anything. The only exception to this rule is the first getter callback (if
    multiple getter callbacks exist), which should return the value of the property.

    Example usage:

        >>> from numbers import Integral
        >>> from utils import attr
        >>> from utils.interval import Interval
        >>> from utils.properties import CustomProperty

        >>> class foo(object):
        ...     x = CustomProperty(attr.getter("_x"), attr.setter("_x"))
        ...     x.has_type(Integral)
        ...     x.has_domain(Interval(0, 100))

        >>> f = foo()
        >>> f.x = 3    # okay
        >>> f.x += 96  # okay
        >>> f.x += 1   # ValueError: out of domain
        >>> f.x = 0.3  # TypeError: not an int
        >>> del f.x    # AttributeError: cannot delete
        >>> print f.x  # prints 99

    """
    __slots__ = ()
    __get__ = property.__get__
    __set__ = property.__set__
    __delete__ = property.__delete__

    def getter(self, fnc):
        """Same as property.getter(), but this method works in-place instead of creating a new
        property."""
        property.__init__(self, fnc, self.fset, self.fdel, self.__doc__)
        return self

    def setter(self, fnc):
        """Same as property.setter(), but this method works in-place instead of creating a new
        property."""
        property.__init__(self, self.fget, fnc, self.fdel, self.__doc__)
        return self

    def deleter(self, fnc):
        """Same as property.deleter(), but this method works in-place instead of creating a new
        property."""
        property.__init__(self, self.fget, self.fset, fnc, self.__doc__)
        return self

    def on_get(self, fnc, before=False):
        """Function/method decorator to add a function to be called when the property is retrieved.
        Note that the first getter function is responsible for computing and returning the actual
        value of the property."""
        if fnc is None:
            return partial(self.on_get, before=before)
        if self.fget is None:
            self.getter(fnc)
        elif isinstance(self.fget, MultiCall):
            if before:
                self.fget.insert(0, fnc)
            else:
                self.fget.append(fnc)
        else:
            self.getter(MultiCall([self.fget, fnc], return_mode=MultiCall.FIRST_RESULT))
            if before:
                self.fget.reverse()
        return self

    def on_set(self, fnc=None, before=True):
        """Function/method decorator to add a function to be called when the property is assigned
        a new value."""
        if fnc is None:
            return partial(self.on_set, before=before)
        if self.fset is None:
            self.setter(fnc)
        elif isinstance(self.fset, MultiCall):
            if before:
                self.fset.insert(0, fnc)
            else:
                self.fset.append(fnc)
        else:
            self.setter(MultiCall([self.fset, fnc]))
            if before:
                self.fset.reverse()
        return self

    def on_delete(self, fnc, before=True):
        """Function/method decorator to add a function to be called when the property is deleted.
        """
        if fnc is None:
            return partial(self.on_delete, before=before)
        if self.fdel is None:
            self.deleter(fnc)
        elif isinstance(self.fdel, MultiCall):
            if before:
                self.fdel.insert(0, fnc)
            else:
                self.fdel.append(fnc)
        else:
            self.deleter(MultiCall([self.fdel, fnc]))
            if before:
                self.fdel.reverse()
        return self

    # --------------------------------------------------------------------------
    # Methods for attaching builtin callback functions
    def has_type(self, cls, none_allowed=False):
        """Set a type for the value of this property. 'cls' can be a type or tuple of types, as in
        utils.misc.check_type() (actually this function is called to check the type of the value).
        'none_allowed' is pretty much self-explanatory.
        Returns the property object."""
        def type_check(obj, val):
            check_type(val, cls, none_allowed)
        self.on_set(type_check, before=True)
        return self

    def has_domain(self, domain):
        """Set a domain for the value of this property. The domain can be any container or any
        object defining a __contains__() method (e.g. utils.interval.Interval).
        Returns the property object."""
        def domain_check(obj, val):
            if val not in domain:
                raise ValueError("custom property value outside domain: %r" % (val,))
        self.on_set(domain_check, before=True)
        return self


def tuple_property(attrs, getter=True, setter=True, deleter=True, doc=None):
    """Creates a simple property that corresponds to a tuple of other attributes or properties."""
    if getter:
        def getter(obj):
            return tuple(getattr(obj, attr) for attr in attrs)
    else:
        getter = None

    if setter:
        def setter(obj, values):
            if len(values) != len(attrs):
                raise ValueError("number of values does not match number of attributes")
            for attr, value in izip(attrs, values):
                setattr(obj, attr, value)
    else:
        setter = None

    if deleter:
        def deleter(obj):
            for attr in attrs:
                delattr(obj, attr)
    else:
        deleter = None
    return property(getter, setter, deleter, doc)

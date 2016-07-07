from __future__ import absolute_import
from copy import copy as shallowcopy, deepcopy
import itertools
import re

from utils.call import CoopCall


def blank_instance(cls):
    """Creates a new blank object without the initialization procedure (__new__() -> __init__())
    automatically executed when creating instances by calling the class constructor. Also, since
    the __new__() method is called without arguments, the new object will be completely blank but
    bound to the argument class.
    This is very useful for example when we wish to create a deep copy of an object which inherits
    attributes from several classes. First we create an empty instance of the most specific class,
    and then each superclass is passed the instance to fill in its own attributes.
    """
    return cls.__new__(cls)


def fetch_copy(obj, memo, factory=None):
    """To be used with __deepcopy__(). This should be passed the object being copied as well as
    deepcopy's memo, which is used to ensure that only one copy of each object is made even if
    there are reference cycles. If an object has already been added to 'memo' as the copy of
    'obj', the clone is returned, otherwise a new instance is created, added to 'memo' (keyed by
    'obj's id), and returned. The creation of the new instance can be controlled through the
    'factory' argument, which should be a function taking the source object as its only argument.
    If no factory is provided, blank_instance() is used."""
    try:
        clone = memo[id(obj)]
    except KeyError:
        clone = blank_instance(type(obj)) if factory is None else factory(obj)
        memo[id(obj)] = clone
    return clone


def coop_deepcopy(obj, memo=None, classes=None, **options):
    """A cooperative copy function for supporting deepcopy operations of objects with complex
    inheritance graphs (e.g. involving multiple inheritance)."""
    if memo is None:
        memo = {}
    if len(options) > 0:
        memo.update(options)
    clone = fetch_copy(obj, memo)
    if classes is None:
        classes = reversed(type(obj).mro())
    for _clone in CoopCall(classes, obj).__deepcopy__(memo):
        if _clone is not clone:
            raise ValueError("mismatch in object returned by cooperative __deepcopy__()")
    return clone


def bases_deepcopy(obj, memo=None, cls=None, reverse=False, **options):
    """Similar to coop_deepcopy(), this function does a cooperative __deepcopy__() call using the
    base classes of 'cls'. If 'cls' is not provided, it defaults to the object's type."""
    if cls is None:
        cls = type(obj)
    bases = reversed(cls.__bases__) if reverse else cls.__bases__
    return coop_deepcopy(obj, memo, bases, **options)


def deepcopy_into(src, tgt=None, memo=None, **options):
    """This helper function can be used to make invoke deepcopy using a specified object as the
    target of the copy (i.e. attributes of 'src' are copied *into* 'tgt'). If no target is
    specified, a simple deepcopy of 'src' is made.
    However, when a target is specified, the source object must provide a __deepcopy__() method,
    since calling deepcopy() with a memo dictionary containing a key for the source object would
    return immediately. Instead, the source object's __deepcopy__() method is called, and can then
    use fetch_copy() to retrieve the target object and modify it accordingly."""
    if memo is None:
        memo = dict()
    if len(options) > 0:
        memo.update(options)
    if tgt is not None:
        if id(src) in memo and memo[id(src)] is not tgt:
            raise Exception("a different clone object already exists for the source object")
        memo[id(src)] = tgt
        return src.__deepcopy__(memo)
    return deepcopy(src, memo)


# constant used to indicate that all attributes of an object should be copied
ALL_ATTRS = object()


def smart_copy(obj, memo=None, shared_attrs=(), shallowcopy_attrs=(), deepcopy_attrs=(),
               check_intersections=True, **options):
    """This function can be used as a direct replacement of __deepcopy__ in classes wishing to
    provide their own implementation. It uses 'deepcopy_attrs' and 'shallowcopy_attrs' to determine
    which object attributes should be deep-copied and those which should be shallow-copied."""
    # determine which attributes are shared, and which to make shallow or deep copies of
    shared_attrs = _determine_attr_set(shared_attrs, obj)
    shallowcopy_attrs = _determine_attr_set(shallowcopy_attrs, obj)
    deepcopy_attrs = _determine_attr_set(deepcopy_attrs, obj)
    # check if all attribute sets are empty
    if len(shared_attrs) == 0 and len(shallowcopy_attrs) == 0 and len(deepcopy_attrs) == 0:
        raise Exception("all copy sets are empty - nothing to copy")
    # check for intersections between attribute sets
    if check_intersections:
        attr_sets = [set(shared_attrs), set(shallowcopy_attrs), set(deepcopy_attrs)]
        for attr_set1, attr_set2 in itertools.combinations(attr_sets, 2):
            conflicting_attrs = attr_set1.intersection(attr_set2)
            if len(conflicting_attrs) > 0:
                raise Exception("intersection between attribute sets - %s" % (conflicting_attrs,))
    # initialize memo if necessary, and update it with the provided options
    if memo is None:
        memo = {}
    if len(options) > 0:
        memo.update(options)
    # fetch or create a clone object and fill it
    clone = fetch_copy(obj, memo)
    for attr in shared_attrs:
        setattr(clone, attr, getattr(obj, attr))
    for attr in shallowcopy_attrs:
        setattr(clone, attr, shallowcopy(getattr(obj, attr)))
    for attr in deepcopy_attrs:
        setattr(clone, attr, deepcopy(getattr(obj, attr), memo))
    return clone


def _determine_attr_set(attr_set, obj):
    """Auxiliary function used by smart_copy().
        - If 'attr_set' is a string, this function interprets it as a regular expression that is
        matched (using re.match(), not re.search()) against 'obj's attributes to determine the
        actual set of attributes.
        - If 'attr_set' is 'ALL_ATTRS', the set of attributes is equal to the set of keys in 'obj's
        dictionary. NOTE: this only works with objects that have a __dict__.
        - If 'attr_set' is None, it is replaced by an empty attribute set."""
    if attr_set is None:
        attr_set = ()
    elif attr_set is ALL_ATTRS:
        attr_set = obj.__dict__.keys()
    elif isinstance(attr_set, str):
        regex = re.compile(attr_set)
        attr_set = {attr for attr in obj.__dict__.iterkeys() if regex.match(attr) is not None}
    return attr_set


def _test():
    A = B = None

    class A(object):
        def __init__(self, a=1):
            self.a = a

        def __repr__(self):
            return "%s-%s" % (type(self).__name__, self.info())

        def info(self):
            return self.a

        def __deepcopy__(self, memo):
            clone = smart_copy(self, memo, deepcopy_attrs=["a"])
            if memo.get("incr", True):
                clone.a += 1
            return clone

        deepcopy = deepcopy_into

    class B(A):
        def __init__(self, a=1, b=2):
            A.__init__(self, a)
            self.b = b

        def info(self):
            return self.a, self.b

        def __deepcopy__(self, memo):
            memo.setdefault("incr", False)
            clone = fetch_copy(self, memo)
            coop_deepcopy(self, memo, B.__bases__)
            clone.b = deepcopy(self.b, memo)
            return clone

    a = A()
    b = B()
    c = b.deepcopy(incr=True)
    return a, b, c

__builtin_str__ = str

def pretty_str(obj, info=None):
    """This function can be used as a default implementation of __str__() in user-defined classes. 
    Classes using this should provide an __info__() method (or directly provide the 'info' part as 
    an argument to this function)."""
    if info is None:
        info = obj.__info__()
    return "%s(%s)" % (type(obj).__name__, info)
    
    
def pretty_repr(obj, str=None):
    """Default implementation of __repr__() for user-defined classes. Simply uses the object's 
    string representation (str(obj)) and adds the object's memory address."""
    if str is None:
        str = __builtin_str__(obj)
    return "<%s @%08X>" % (str, id(obj))
    
    
def build_object_info(obj, attrs=None, fmt="%s=%r", sep=", "):
    """Builds a string containing a description of a list of attributes of 'obj'. If 'attrs' is 
    not provided (i.e. None), this function looks for it in the object's '__info_attrs__' attribute 
    (which should be a collection of attribute names). 
    Separator and format strings may be specified to customize how the items are joined, and how 
    each (attr, value) pair is formatted, respectively."""
    if attrs is None:
        attrs = obj.__info_attrs__
    return build_info(((attr, getattr(obj, attr)) for attr in attrs), fmt, sep)
    
    
def build_info(pairs, fmt="%s=%r", sep=", "):
    if isinstance(pairs, dict):
        pairs = pairs.iteritems()
    return sep.join(fmt % (key, value) for key, value in pairs)
    
    
def prettify_class(cls):
    """Sets the defaults of __str__, __repr__, __info__, and __info_attrs__ on the argument class. 
    This function can be used as a class decorator or called as a normal function."""
    if cls.__str__ is cls.__base__.__str__:
        cls.__str__ = pretty_str
    if cls.__repr__ is cls.__base__.__repr__: 
        cls.__repr__ = pretty_repr
    if not hasattr(cls, "__info__"):
        cls.__info__ = build_object_info
    if not hasattr(cls, "__info_attrs__"):
        cls.__info_attrs__ = []
    return cls
    
    
class PrettyMeta(type):
    """Metaclass for pretty classes."""
    def __init__(cls, name, bases, dic):
        type.__init__(cls, name, bases, dic)
        prettify_class(cls)
        
        
class PrettyBase(object):
    """Base class for pretty str() and repr()."""
    __str__        = pretty_str
    __repr__       = pretty_repr
    __info__       = build_object_info
    __info_attrs__ = []
    
    
def _test():
    class foo(object):
        __info_attrs__ = ["x", "y"]
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            
    prettify_class(foo)
    f = foo(x=234, y=40)
    print "created object f = foo(x=234, y=40)"
    print "f.__info__() -->", f.__info__()
    print "str(f) -->", str(f)
    print "repr(f) -->", repr(f)
    return f
    
    
def _test2():
    class bar(object):
        __metaclass__ = PrettyMeta
        __info_attrs__ = ["a", "b"]
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            
    b = bar(a="oh lord", b="o_O")
    print """created object b = bar(a="oh lord", b="o_O")"""
    print "b.__info__() -->", b.__info__()
    print "str(b) -->", str(b)
    print "repr(b) -->", repr(b)
    return b
    
    

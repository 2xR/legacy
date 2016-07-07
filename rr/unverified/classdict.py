"""A classdict is nothing more than a dictionary which is an attribute of a class, and other 
classes in its hierarchy tree can also have dictionaries bound to the same attribute name. The idea 
is that subclasses can define a dictionary under the same name, but include only the data that is 
actually redefined (instead of creating a copy of the base class' dictionary and adding in the new
values).
"""
from utils.misc import UNDEF
from utils import multidict


def iter(start_cls, dict_name, reverse=False):
    """An iterator over the classdicts of 'start_cls's class hierarchy. The classes are visited in 
    the order output by mro() by default, but can be reversed by passing 'reverse=True'.
    This function generates a sequence of dictionaries."""
    classes = start_cls.mro()
    if reverse:
        classes.reverse()
    for cls in classes:
        try:
            d = cls.__dict__[dict_name]
        except KeyError:
            continue
        if isinstance(d, dict):
            yield d
            
            
def lookup(start_cls, dict_name, dict_key, default=UNDEF):
    """Look for a key in the classdicts specified by 'start_cls' and 'dict_name'. Returns the first
    found value or raises KeyError."""
    return multidict.lookup(iter(start_cls, dict_name), dict_key, default)
    
    
def has_key(start_cls, dict_name, dict_key):
    """Return True if 'dict_key' can be found in the specified classdicts, False otherwise."""
    return multidict.has_key(iter(start_cls, dict_name), dict_key)
    
    
def merge(start_cls, dict_name):
    """The merge() function creates a dictionary with the values from all classdicts, associating 
    each key to the value appearing in the most specific classdict, i.e. values defined in 
    subclasses override values defined in base classes."""
    return multidict.merge(iter(start_cls, dict_name, reverse=True))
    
    
def _test():
    import string
    
    class A(object):
        foo = {x: x**2 for x in xrange(5)}
    class B(A):
        foo = {c: c.upper() for c in string.lowercase}
        foo[0] = "bar"
        foo[3] = "gez"
        
    print "classdict viewed from A", merge(A, "foo")
    print "classdict viewed from B", merge(B, "foo")
    for k in merge(B, "foo"):
        v_A = lookup(A, "foo", k, "<missing key>")
        v_B = lookup(B, "foo", k, "<missing key>")
        print "Lookup %s from A and B --> %s, %s" % (k, v_A, v_B)
    return A, B
    

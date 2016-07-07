"""
This module provides classes implementing the observer design pattern. It is so useful and 
common that it should be readily available to users.

TODO: More documentation and examples.
"""
from bisect import bisect_right

from utils.misc import INF, UNDEF, callable_name


class Observable(object):
    """Class implementing an observable variable, i.e. these objects may be monitored for changes 
    automatically using Observer objects (constructed through the Observable.observe() method). 
    An Observer object may have a condition function, which is a boolean function that receives 
    the variable's value and verifies a particular condition on the value. When the condition 
    function returns True, the observer's callback function is called with the current value as 
    argument.
    Additionally, observers have a priority attribute which defines the order in which they are 
    executed when the variable is changed. A 'sticky' attribute is also available. This attribute 
    is used to define behavior during activation. A non-sticky Observer is removed from the 
    variable's list of observers when it is satisfied, whereas a sticky observer remains in this 
    list until manually removed. This means that a sticky observer may activate any number of 
    times, and a non-sticky observers activates at most once."""
    def __init__(self, value=None):
        self.value = value
        self.observers = list()
        
    def __repr__(self):
        return ("<%s[%d observers] %s (%08x)>" % 
                (type(self).__name__, len(self.observers), self.value, id(self)))
        
    def clear(self):
        self.observers = list()
        self.value = None
        
    def get(self):
        return self.value
        
    def set(self, value):
        self.value = value
        if len(self.observers) > 0:
            self.dispatch()
            
    def dispatch(self):
        """Inform observers of the current value of this object. Observers are informed from small 
        to large priority. Observers removed by the activation of a previous dispatch are not 
        evaluated."""
        value = self.value
        for observer in list(self.observers):
            if not observer.__deployed:
                continue
            observer.check(value)
            
    def observe(self, callback, condition=None, priority=0.0, sticky=True, owner=None):
        observer = Observer(self, callback, condition, priority, sticky, owner)
        observer.__deployed = False
        observer.start()
        return observer
        
    def _insert(self, observer):
        try:
            if observer.__deployed:
                raise ValueError("duplicate attempt to deploy observer")
        except AttributeError:
            pass
        priorities = [obs.__priority for obs in self.observers]
        index = bisect_right(priorities, observer.priority)
        self.observers.insert(index, observer)
        observer.__priority = observer.priority
        observer.__deployed = True
        observer.check(self.value)
        
    def _remove(self, observer):
        self.observers.remove(observer)
        observer.__deployed = False
        
    # --------------------------------------------
    # Observer factory methods
    def lt(self, value, callback, priority=0.0, sticky=False, owner=None):
        def condition(v):
            return v < value
        condition.__name__ = "lt_" + str(value)
        return self.observe(callback, condition, priority, sticky, owner)
        
    def leq(self, value, callback, priority=0.0, sticky=False, owner=None):
        def condition(v):
            return v <= value
        condition.__name__ = "leq_" + str(value)
        return self.observe(callback, condition, priority, sticky, owner)
        
    def gt(self, value, callback, priority=0.0, sticky=False, owner=None):
        def condition(v):
            return v > value
        condition.__name__ = "gt_" + str(value)
        return self.observe(callback, condition, priority, sticky, owner)
        
    def geq(self, value, callback, priority=0.0, sticky=False, owner=None):
        def condition(v):
            return v >= value
        condition.__name__ = "geq_" + str(value)
        return self.observe(callback, condition, priority, sticky, owner)
        
    def eq(self, value, callback, priority=0.0, sticky=False, owner=None):
        def condition(v):
            return v == value
        condition.__name__ = "eq_" + str(value)
        return self.observe(callback, condition, priority, sticky, owner)
        
    def neq(self, value, callback, priority=0.0, sticky=False, owner=None):
        def condition(v):
            return v != value
        condition.__name__ = "neq_" + str(value)
        return self.observe(callback, condition, priority, sticky, owner)
        
    def member_of(self, value, callback, priority=0.0, sticky=False, owner=None):
        def condition(v):
            return v in value
        condition.__name__ = "in_" + str(value)
        return self.observe(callback, condition, priority, sticky, owner)
        
    def not_member_of(self, value, callback, priority=0.0, sticky=False, owner=None):
        def condition(v):
            return v not in value
        condition.__name__ = "not_in_" + str(value)
        return self.observe(callback, condition, priority, sticky, owner)
        
    def contains(self, value, callback, priority=0.0, sticky=False, owner=None):
        def condition(v):
            return value in v
        condition.__name__ = "contains_" + str(value)
        return self.observe(callback, condition, priority, sticky, owner)
        
    def not_contains(self, value, callback, priority=0.0, sticky=False, owner=None):
        def condition(v):
            return value not in v
        condition.__name__ = "not_contains_" + str(value)
        return self.observe(callback, condition, priority, sticky, owner)
        
        
class ObservableAttr(object):
    def __init__(self, value=None):
        self.value = value
        
    def __set__(self, obj, value):
        self.get(obj).set(value)
        
    def __get__(self, obj, owner):
        return self if obj is None else self.get(obj).value
        
    def __delete__(self, obj):
        del obj.__observable_attr[self]
        if len(obj.__observable_attr) == 0:
            del obj.__observable_attr
            
    def get(self, obj):
        return obj.__observable_attr[self]
        
    def init(self, obj):
        try:
            obj.__observable_attr[self] = Observable(self.value)
        except AttributeError:
            obj.__observable_attr = {self: Observable(self.value)}
            
            
Observable.Attr = ObservableAttr


class Observer(object):
    """Observer objects are used to execute arbitrary code when a Observable object's value is 
    changed and meets a given condition. Please refer to the documentation of the Observable 
    class for more details."""
    def __init__(self, observable, callback, condition=None, 
                 priority=0.0, sticky=False, owner=None):
        self.observable = observable
        self.callback = callback
        self.condition = condition
        self.priority = priority
        self.sticky = sticky
        self.owner = owner
        self.match = None
        
    def __repr__(self):
        condition = "" if self.condition is None else (" if " + callable_name(self.condition))
        owner = ("%s:" % self.owner) if self.owner is not None else ""
        callback = callable_name(self.callback)
        return ("<%s%s >> %s%s() [P=%s, S=%s] (%08x)>" % 
                (type(self).__name__, condition, owner, callback, 
                 self.priority, self.sticky, id(self)))
        
    def start(self):
        self.observable._insert(self)
        
    def stop(self):
        self.observable._remove(self)
        
    def check(self, value=UNDEF):
        if value is UNDEF:
            value = self.observable.value
        if self.condition is None or self.condition(value):
            if not self.sticky:
                self.stop()
            self.match = value
            self.callback(self)
            return True
        return False
        
        
def _test():
    from random import uniform, choice
    
    x = Observable(10)
    
    def foo(o):
        print "%s activated by value %s" % (o, o.match)
        
    x.member_of(range(8), foo, priority=uniform(-1, +1), sticky=choice([True, False]))
    x.not_member_of(range(10, 15), foo, priority=uniform(-1, +1), sticky=choice([True, False]))
    x.eq(3, foo, priority=uniform(-1, +1), sticky=choice([True, False]))
    x.neq(10, foo, priority=uniform(-1, +1), sticky=choice([True, False]))
    x.lt(5, foo, priority=uniform(-1, +1), sticky=choice([True, False]))
    x.geq(20, foo, priority=uniform(-1, +1), sticky=choice([True, False]))
    
    for v in (8, 5, 4, 3, 121):
        print "setting x to", v
        x.set(v)
    
    class Foo(object):
        x = Observable.Attr(0.0)
        y = Observable.Attr(0.0)
        
        def __init__(self, x, y):
            Foo.x.init(self)
            Foo.y.init(self)
            self.x = x
            self.y = y
            
    return Foo, x


from khronos.des.primitives.action import Action
from khronos.utils import Check

class Poll(Action):
    """This primitive action type is specifically designed to be used with Checkable objects from  
    the utils package, making a very powerful combination where components can block until a given
    condition on the Checkable's value is observed. The first argument should be a condition 
    function taking a value as only argument and returning a boolean value, and the second 
    argument should be a Checkable object. An optional priority value may be passed to the 
    constructor to manipulate the order of checks in the Checkable object. This primitive succeeds 
    when the check activates, making the process block until the condition on the Checkable is 
    satisfied."""
    def __init__(self, condition, checkable, priority=0.0):
        Action.__init__(self)
        self.check = Check(condition, self.succeed, priority, sticky=False)
        self.checkable = checkable
        self.result = None
        
    def __info__(self):
        parts = [self.check.condition.__name__]
        if self.result is not None:
            parts.append(str(self.result))
        return " -> ".join(parts)
        
    def reset(self):
        self.result = None
        
    def deploy(self):
        self.checkable.insert(self.check)
        
    def retract(self):
        self.checkable.remove(self.check)
        
    def succeed(self, value):
        self.result = value
        self.succeed()
        
    # -----------------------------------------------------
    # Poll factory functions ------------------------------
    @staticmethod
    def less_than(value, checkable, priority=0.0):
        def condition(v):
            return v < value
        condition.__name__ = "< %s" % (value,)
        return Poll(condition, checkable, priority)
        
    @staticmethod
    def less_or_equal(value, checkable, priority=0.0):
        def condition(v):
            return v <= value
        condition.__name__ = "<= %s" % (value,)
        return Poll(condition, checkable, priority)
        
    @staticmethod
    def greater_than(value, checkable, priority=0.0):
        def condition(v):
            return v > value
        condition.__name__ = "> %s" % (value,)
        return Poll(condition, checkable, priority)
        
    @staticmethod
    def greater_or_equal(value, checkable, priority=0.0):
        def condition(v):
            return v >= value
        condition.__name__ = ">= %s" % (value,)
        return Poll(condition, checkable, priority)
        
    @staticmethod
    def equal_to(value, checkable, priority=0.0):
        def condition(v):
            return v == value
        condition.__name__ = "== %s" % (value,)
        return Poll(condition, checkable, priority)
        
    @staticmethod
    def not_equal_to(value, checkable, priority=0.0):
        def condition(v):
            return v != value
        condition.__name__ = "!= %s" % (value,)
        return Poll(condition, checkable, priority)
        
    @staticmethod
    def member_of(values, checkable, priority=0.0):
        def condition(v):
            return v in values
        condition.__name__ = "in %s" % (values,)
        return Poll(condition, checkable, priority)
        
    @staticmethod
    def not_member_of(values, checkable, priority=0.0):
        def condition(v):
            return v not in values
        condition.__name__ = "not in %s" % (values,)
        return Poll(condition, checkable, priority)
        
    @staticmethod
    def contains(value, checkable, priority=0.0):
        def condition(v):
            return value in v
        condition.__name__ = "contains %s" % (value,)
        return Poll(condition, checkable, priority)
        
    @staticmethod
    def not_contains(value, checkable, priority=0.0):
        def condition(v):
            return value not in v
        condition.__name__ = "not contains %s" % (value,)
        return Poll(condition, checkable, priority)
        

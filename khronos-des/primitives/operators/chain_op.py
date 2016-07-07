from types import GeneratorType

from khronos.des.primitives.action import Action, UNDEPLOYED, DEPLOYED
from khronos.utils import Call

class ChainGetter(Action):
    """This action should only be used inside chains to access the Chain object."""
    def start(self):
        self.parent.step(self.parent)
        
class ChainResult(Action):
    """Action used to set an arbitrary object to a chain's result attribute. The ChainResult 
    class is made indirectly available through the 'result' attribute of the Chain class. 
    Example:
        x = [123, "abc", (self,)]
        yield Chain.result(x)"""
    def __init__(self, value):
        Action.__init__(self)
        self.value = value
        
    def start(self):
        self.parent.result = self.value
        self.parent.step(self.value)
        
class ChainSuccess(StopIteration):
    """This exception class is used to force a success of the chain. If it is raised inside a 
    chain's generator function, the chain object will succeed(). The ChainSuccess class is 
    made available through the 'success' attribute of the Chain class. Example:
        @Chain
        def foo(self):
            yield 10 * MINUTE
            if condition_to_succeed():
                raise Chain.success()
            else:
                ...
    Note that this is nothing more than a StopIteration exception. It exists for consistency 
    and increased readability, but you could obtain the same result by explicitly raising 
    StopIteration, simply using an empty return, or in most cases just let the generator 
    function run to the end, where a StopIteration exception is implicitly raised. However, 
    it is arguably better to raise a Chain.success() instead of putting an empty return or 
    raising StopIteration, because that way whoever reads the program will think/know that the 
    chain will succeed, and return/StopIteration do not give this idea to readers."""
    
class ChainFailure(Exception):
    """This exception class is used to force a failure of the chain. If it is raised inside a 
    chain's generator function, the chain object will fail(). The ChainFailure class is made 
    available through the 'failure' attribute of the Chain class. Example:
        @Chain
        def foo(self):
            yield 10 * MINUTE
            if not condition_to_continue():
                raise Chain.failure()
            else:
                ..."""
    
class Chain(Action):
    get     = ChainGetter
    result  = ChainResult
    success = ChainSuccess
    failure = ChainFailure
    
    @classmethod
    def from_constructor(cls, constructor):
        """This is the actual constructor of the Chain class, because the __new__() special 
        function works as a convenient function decorator. In fact, action chains should only 
        be created by calling Chain-decorated functions, and manual creation of chain objects 
        should be avoided. To manually create a Chain object from a callable, simply write
            c = Chain.from_constructor(my_callable)
        instead of 
            c = Chain(my_callable)
        since the latter version will actually return a new function (the decorated version) which 
        works as a chain factory."""
        self = Action.__new__(cls)
        Action.__init__(self)
        self.constructor = constructor
        self.generator = None
        self.current = None
        self.result = None
        return self
        
    @classmethod
    def from_generator(cls, generator):
        """This creates a Chain object given a generator. Note that chain objects created with 
        this method are not reproducible (i.e. can be executed only once), since the constructor 
        will always return the same generator object."""
        def constructor_fnc():
            return generator
        constructor_fnc.__name__ = generator.__name__ + "!!"
        constructor_fnc.__doc__ = generator.__doc__
        return cls.from_constructor(constructor_fnc)
        
    def __info__(self):
        parts = [self.constructor.__name__]
        if self.result is not None:
            parts.append(str(self.result))
        return " -> ".join(parts)
        
    def reset(self):
        self.generator = None
        self.current = None
        self.result = None
        
    def deploy(self):
        try:
            generator = self.constructor()
        except StopIteration:
            Action.succeed(self)
        else:
            if not isinstance(generator, GeneratorType):
                raise TypeError("invalid chain - constructor did not return a generator")
            self.generator = generator
            self.step()
            
    def retract(self):
        self.current.cancel()
        
    def step(self, send_value=None):
        try:
            result = self.generator.send(send_value)
        except StopIteration:
            Action.succeed(self)
        except ChainFailure:
            Action.fail(self)
        else:
            if not isinstance(result, Action):
                result = Action.convert(result)
            if result is not self.current:
                self.deployment = UNDEPLOYED
                self.current = result
                self.current.link(self)
                self.deployment = DEPLOYED
            self.current.start()
            
    def succeed(self):
        self.current.succeed()
        
    def fail(self):
        self.current.fail()
        
    def child_activated(self, child): 
        if child is not self.current:
            raise ValueError("invalid child action provided")
        self.step(child)
        
    child_succeeded = child_activated
    child_failed    = child_activated
    # -----------------------------------------------------
    # Function decorators
    def __new__(cls, fnc):
        """The default class constructor works as a function decorator for functions or methods 
        defining action chains. When the decorated function is called, an unbound Chain object is 
        created and returned.
            @Chain
            def my_chain(self):
                do_stuff_here"""
        def new_fnc(*args, **kwargs):
            chain = cls.from_constructor(Call(fnc, *args, **kwargs))
            return chain
        new_fnc.__name__ = fnc.__name__
        new_fnc.__doc__ = fnc.__doc__
        return new_fnc
        
    @classmethod
    def bound(cls, fnc):
        """Like the __new__() decorator, this one also allows automatic creation of action chains 
        when the decorated method (or function) is called, with the difference that the created 
        chain is bound to the first positional argument. This usage is appropriate on component 
        *methods*, where the component is always the first positional argument (self)."""
        def new_fnc(*args, **kwargs):
            chain = cls.from_constructor(Call(fnc, *args, **kwargs))
            chain.bind(args[0])  # args[0] is 'self' in object methods
            return chain
        new_fnc.__name__ = fnc.__name__
        new_fnc.__doc__ = fnc.__doc__
        return new_fnc
        

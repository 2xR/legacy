from khronos.des.primitives import Action

class Thread(object):
    """The Thread class implements the capability to interact with a Simulator object and execute 
    blocking actions (primitives), but in a way that is not as heavy as the Process class (without 
    names and hierarchy). Therefore, threads cannot be attached to a Simulator object like 
    processes, but they can be used for simple entities that are dynamically created during a 
    simulation."""
    def __init__(self, sim=None, *args, **kwargs):
        self.__simulator = sim
        self.__action = Action()
        self.__running = False
        self.__locked = False
        self.constructor(*args, **kwargs)
        
    def __repr__(self):
        state = "Running" if self.__running else "Idle"
        locked = "(locked)" if self.__locked else ""
        return "<%s%s %s object at 0x%08x>" % (state, locked, self.__class__.__name__, id(self))
        
    # -----------------------------------------------------
    # Basic thread properties -----------------------------
    @property
    def sim(self):
        return self.__simulator
        
    @sim.setter
    def sim(self, simulator):
        self.__simulator = simulator
        
    @property
    def action(self):
        return self.__action
        
    @property
    def running(self):
        return self.__running
        
    # -----------------------------------------------------
    # Basic thread methods -------------------------------
    def constructor(self, **kwargs):
        """Default constructor function. It adds all passed keyword arguments to the object 
        attribute dictionary. This method should be redefined for different component classes
        according to the arguments that you want the constructor to admit. For example, if you 
        want a class that only takes optional 'x' and 'y' arguments,
            class Point2d(Thread):
                def constructor(self, x=0, y=0):
                    self.x = x
                    self.y = y
                ...
        Now this class only admits 'x' and 'y' (in addition to 'sim') as arguments to its 
        constructor."""
        if len(kwargs) > 0:
            self.__dict__.update(kwargs)
            
    def execute(self, action):
        """Bind and deploy simulation primitives. Binding an action means associating the thread
        to the action (as its owner), and deploying refers to starting the action, e.g. for a 
        delay, deployment means inserting the delay into the simulation schedule."""
        if not self.__running:
            raise ValueError("idle %s attempting to execute action" % (self.__class__.__name__,))
        if not isinstance(action, Action):
            action = Action.convert(action) 
        if action.parent is not None:
            raise ValueError("calling execute() on non-root action")
        if action.owner is not self:
            action.bind(self)
        self.__action.cancel()
        self.__action = action
        action.start()
        return action
        
    def start(self, start_fnc=None):
        """Start a thread's simulation behavior. This basically means that the thread can start 
        executing actions. A start function can be provided, making the thread's behavior start 
        at that function. If no start function is given, the initialize() method is called. This 
        method locks the thread so that start() or stop() do not work until it exits.
        IMPORTANT NOTE: start() and stop() should NOT be redefined in subclasses. Instead, the 
        methods that should be redefined are initialize() and finalize(), as the start and end 
        points of a thread's simulation behavior, respectively."""
        if not self.__running and not self.__locked:
            self.__locked = True
            self.__running = True
            self.__action = Action()
            if start_fnc is None:
                start_fnc = self.initialize
            result = start_fnc()
            if result is not None:
                self.execute(result)
            self.__locked = False
            
    def stop(self, stop_fnc=None):
        """Stop a thread's simulation behavior. After being stopped, the thread can no longer 
        execute actions. A stop function may be provided here, to be called without arguments 
        by stop(). Its role should be to release any acquired system resources (e.g. files) 
        and/or present simulation results. If no stop function is provided, the finalize() 
        method is called by default."""
        if self.__running and not self.__locked:
            self.__locked = True
            self.__running = False
            self.__action.cancel()
            if stop_fnc is None:
                stop_fnc = self.finalize
            stop_fnc()
            self.__locked = False
            
    def initialize(self):
        pass
        
    def finalize(self):
        pass
        

from khronos.des.primitives.action import Action, SUCCEEDED, FAILED

class Observer(Action):
    """This primitive observes the completion state of another action, and activates with the 
    same state. This appears useless at first, but it can be used to observe actions bound to 
    different owners (even when already deployed!), thus allowing synchronization among processes.
        As a small example, if we wanted to simulate a multi-threaded program where the main thread
    waits for the completion of several worker threads, we could use the Observer primitive to 
    achieve this, writing something like:
        class MainThread(Simulator):
            def initialize(self):
                print "creating worker threads..."
                threads = [self.launch(WorkerThread(x)) for x in xrange(3)]
                yield And(*[Observer(thread.action) for thread in threads])
                print "all threads finished"
                
        class WorkerThread(Process):
            def initialize(self):
                return self.sim.rng.randint(100, 1000)
    """
    def __init__(self, target):
        Action.__init__(self)
        self.target = target
        
    def __info__(self):
        return "%s by %s" % (self.target, self.target.owner)
        
    def deploy(self):
        if self.target.completion is SUCCEEDED:
            self.succeed()
        elif self.target.completion is FAILED:
            self.fail()
        else:
            if self.target.observers is None:
                self.target.observers = [self]
            else:
                self.target.observers.append(self)
                
    def retract(self):
        self.target.observers.remove(self)
        if len(self.target.observers) == 0:
            self.target.observers = None
            
    def target_succeeded(self, target):
        if target is not self.target:
            raise ValueError("invalid target action provided")
        self.succeed()
        
    def target_failed(self, target):
        if target is not self.target:
            raise ValueError("invalid target action provided")
        self.fail()
        

from khronos.des.primitives.action import Action, DEPLOYING, DEPLOYED

class Delay(Action):
    def __init__(self, length, priority=0.0):
        Action.__init__(self)
        self.length = length
        self.priority = priority
        
    def __info__(self):
        return self.length
        
    def deploy(self):
        raise Exception("this method is implemented by the simulator")
        
    def retract(self):
        raise Exception("this method is implemented by the simulator")
        
    def finish(self):
        """Called by the simulator when the delay was reached in the event schedule, in order to 
        prevent an invalid attempt to remove it from the schedule at retraction."""
        if self.deployment is not DEPLOYED:
            raise ValueError("cannot finish() - delay is not deployed")
        self.deployment = DEPLOYING
        self.succeed()
        

from khronos.des.primitives.action import Action

class Channel(dict):
    """This class implements a closed channel for asynchronous communication using Signal and 
    Listener primitives. Users are not required to use the primitive classes directly. Instead,
    the listen() and emit() methods should be used.
        TODO: add an example of channel usage.
    """
    def listen(self, *args, **kwargs):
        return Listener(self, *args, **kwargs)
        
    def emit(self, *args, **kwargs):
        return Signal(self, *args, **kwargs)
        
    def _insert(self, listener):
        try:
            self[listener.type].add(listener)
        except KeyError:
            self[listener.type] = set([listener])
        listener.__type = listener.type
        
    def _remove(self, listener):
        listener_set = self[listener.__type]
        listener_set.remove(listener)
        if len(listener_set) == 0:
            del self[listener.__type]
            
    def _broadcast(self, signal):
        noise = signal.owner.sim.rng.random
        for type in (signal.type, None):
            try:
                listeners = self[type]
            except KeyError:
                continue
            else:
                matches = [(l.priority, noise(), l) for l in listeners]
                for p, n, l in sorted(matches):
                    if l.deployed():
                        l.succeed(signal)
                        
class Listener(Action):
    """Implements a wait for a signal. Whenever some process broadcasts a signal with the same 
    type on the same channel, the listener will succeed. If the type is None, the listener will 
    succeed at the first signal on the channel, independently of the signal's type. Listeners also 
    have a 'priority' attribute that can be passed to the constructor. It defines the order by 
    which listeners are activated when a signal triggers multiple listeners simultaneously (high 
    priority first)."""
    def __init__(self, channel, type, priority=0.0):
        Action.__init__(self)
        self.channel = channel
        self.type = type
        self.priority = priority
        self.match = None
        
    def __info__(self):
        return "*" if self.type is None else self.type
        
    def deploy(self):
        self.channel._insert(self)
        
    def retract(self):
        self.channel._remove(self)
        
    def succeed(self, signal):
        self.match = signal
        Action.succeed(self)
        
class Signal(Action):
    """Signals are an instantaneous primitive that allows synchronizing several components 
    listening on the same channel. Signals activate listeners, which make their owners block 
    until a signal of matching type is emitted on the same channel."""
    def __init__(self, channel, type, **payload):
        Action.__init__(self)
        self.channel = channel
        self.type = type
        self.payload = payload
        
    def __info__(self):
        return "".join((self.type, " - ", repr(self.payload)))
        
    def deploy(self):
        self.channel._broadcast(self)
        self.succeed()
        
    def retract(self):
        raise NotImplementedError()
        

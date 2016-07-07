from khronos.utils.deque import Deque

class SignalManager(object):
    def __init__(self):
        self.listeners = {}
        
    def add_listener(self, sig_type, callback, priority=0.0):
        try:
            self.listeners[sig_type].insort((priority, callback))
        except KeyError:
            self.listeners[sig_type] = Deque([(priority, callback)])
            
    def signal(self, sig_type, *args, **kwargs):
        for _, callback in self.listeners.get(sig_type, []):
            callback(*args, **kwargs)
            

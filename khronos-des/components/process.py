from khronos.des.components.component import Component
from khronos.des.components.thread import Thread
from khronos.utils import PQueue

class Process(Thread, Component):
    """This class mixes the functionality of the Component class (hierarchical organization, 
    names, retrieval by path, status) with the Thread class (dynamic simulation behavior)."""
    initialize_priority = 0.0
    finalize_priority   = 0.0
    
    def __init__(self, name=None, parent=None, members=(), *args, **kwargs):
        Component.__init__(self, name, parent, members)
        Thread.__init__(self, *args, **kwargs)
        
    def __repr__(self):
        state = "Running" if self.running else "Idle"
        class_name = self.__class__.__name__
        return "<%s - %s %s object at 0x%08x>" % (self.full_path, state, class_name, id(self))
        
    def start(self, start_fnc=None):
        """Start a process and all its members. Members with positive initialize_priority are 
        started before 'self', with highest priority members being started first. After these 
        members, 'self' is started, and finally, members with non-positive priority are started 
        (lowest priority members first)."""
        before = PQueue()
        after  = PQueue()
        for member in self.members:
            priority = member.initialize_priority 
            (before if priority > 0.0 else after).insert(member, priority)
        before.shuffle(rng=self.sim.rng)
        after.shuffle(rng=self.sim.rng)
        # Start members with positive priority (largest first), then start self, 
        # and finally start members with non-positive priority (smallest first). 
        for member, priority in before.iter_descending():
            member.start()
        Thread.start(self, start_fnc)
        for member, priority in after.iter_ascending():
            member.start()
            
    def stop(self, stop_fnc=None):
        """Stop a process and all its members. Members with positive finalize_priority are 
        stopped before 'self', with highest priority members being stopped first. After these 
        members, 'self' is stopped, and finally, members with non-positive priority are stopped 
        (lowest priority members first)."""
        before = PQueue()
        after  = PQueue()
        for member in self.members:
            priority = member.finalize_priority 
            (before if priority > 0.0 else after).insert(member, priority)
        before.shuffle(rng=self.sim.rng)
        after.shuffle(rng=self.sim.rng)
        # Stop members with positive priority (largest first), then stop self, 
        # and finally stop members with non-positive priority (smallest first). 
        for member, priority in before.iter_descending():
            member.stop()
        Thread.stop(self, stop_fnc)
        for member, priority in after.iter_ascending():
            member.stop()
            
    def rewind(self):
        """Reset a process and its members (order dependent on dict traversal). This method is 
        called by the simulator before starting a new simulation run. rewind() checks the state 
        of the process and calls the reset() method. Process classes can redefine reset(), where 
        they should clear their state from any previous simulation run and reset any attributes  
        necessary at initialization. Before a new simulation run is started, the simulator calls 
        rewind() on all model components before calling start(), so at the initialize() method it  
        is guaranteed that every component has been previously cleared and reinitialized."""
        if not self.running:
            self.sim = self.root
            self.reset()
            for member in self.members:
                member.rewind()
                
    def reset(self):
        pass
        
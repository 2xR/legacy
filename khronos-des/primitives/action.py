from contextlib import contextmanager

UNDEPLOYED = "undeployed"
DEPLOYING  = "deploying"
DEPLOYED   = "deployed"
SUCCEEDED  = "succeeded"
FAILED     = "failed"
CANCELED   = "canceled"

class Action(object):
    """Base class for simulation primitives. Simulation primitives implement dynamic behavior 
    which is performed by the action's owner, like waiting for a given amount of time, sending 
    signals to other processes, requesting a resource, etc. Complex behaviors can be created by 
    building trees of actions ('parent' attribute) using operators such as And, Or, or Chain. 
        The common attributes to all action objects are:
            owner - process/component who is executing the action
            parent - parent action (for compound actions)
            observers - other actions observing the action's completion (None if no observers)
            deployment - for tracking the action's deployment phase
            completion - the action's state of completion
            start_time - simulation time at which the action was started 
            end_time - simulation time at which the action completed (succeed, fail, or cancel)
        Action trees can be built by establishing parent-child relations between actions. Each 
    action in the tree has exactly one 'parent' action, with the root - having no parent - as the 
    only exception to this rule. It is important to note that once an action's parent is set, it 
    cannot be changed.
        During execution, all actions must have an associated 'owner' process (or thread). All 
    actions belonging to the same tree have the same owner, and the root action is set as the 
    'action' attribute of the owner process, thus calling 'owner.action.cancel()' will cancel the 
    entire action tree.
        Each process can have only one (root) action at any time. This doesn't mean that a process
    cannot execute multiple actions simultaneously: they just have to belong to the same action 
    tree, e.g. using a 'And' operator. Whenever a process executes a new root action, its previous 
    root action is canceled if it is ongoing, and the new tree replaces the previous one.
        For tracking the deployment and completion states, actions have two attributes with the 
    same name. Of the three possible completion states, the action enters the simulation stack 
    only in the SUCEEDED or FAILED state, and the parent action and observers are notified of the 
    its completion. If the action is canceled, it is merely retracted, but neither the parent 
    action or any observer is notified of this."""
    def __init__(self):
        self.owner = None
        self.parent = None
        self.observers = None
        self.deployment = UNDEPLOYED
        self.completion = None
        self.start_time = None
        self.end_time = None
        
    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.info())
        
    def __info__(self):
        """The information displayed inside the action's string representation."""
        return ""
        
    @property
    def elapsed_time(self):
        """Return the simulation time elapsed since the action was started. If the action wasn't 
        started yet, then None is returned. If the action has already completed, then the time 
        interval between start and completion is returned."""
        if self.start_time is None:
            return None
        if self.end_time is None:
            return self.owner.sim.time - self.start_time
        return self.end_time - self.start_time
        
    def bind(self, owner):
        """Associate this action to a process. This is a mandatory step before executing the 
        action, since access to a simulator object is obtained through the owner."""
        self.owner = owner
        
    def link(self, parent):
        """Set the action's parent. This is called by the parent action operator (e.g. a Chain).
        The state of the parent and the child action is checked. Both actions must be undeployed, 
        otherwise an exception will be raised. Additionally, if the parent action is already 
        bound to a process, the child is also bound to the same owner."""
        if self.parent is not None:
            raise ValueError("illegal link - parent action cannot be changed")
        if self.owner is not None:
            raise ValueError("illegal link - child action must be unbound")
        if self.deployment is not UNDEPLOYED or parent.deployment is not UNDEPLOYED:
            raise ValueError("cannot link - both actions must be undeployed")
        self.parent = parent
        if parent.owner is not None:
            self.bind(parent.owner)
            
    # -----------------------------------------------------
    def push_to(self, sim, activation_type):
        raise NotImplementedError()
        
    def pop_from(self, sim):
        raise NotImplementedError()
        
    @contextmanager
    def in_stack(self, activation_type):
        sim = self.owner.sim
        self.push_to(sim, activation_type)
        yield
        self.pop_from(sim)
        
    def start(self):
        """Start an action, i.e. deploy the action and manage its state accordingly. Before 
        deployment, the action's reset() method is called. """
        with self.in_stack(" "):
            if self.deployment is not UNDEPLOYED:
                raise ValueError("cannot start() - action is deployed/deploying")
            self.completion = None
            self.start_time = self.owner.sim.time
            self.end_time = None
            self.reset()
            self.deployment = DEPLOYING
            self.deploy()
            if self.completion is None:
                self.deployment = DEPLOYED
                
    def succeed(self):
        """Complete the action successfully. With the action pushed into the simulation stack, 
        the parent action and observers are warned of the action's success."""
        with self.in_stack("S"):
            if self.deployment is UNDEPLOYED:
                raise ValueError("cannot succeed() - action is undeployed")
            if self.deployment is DEPLOYED:
                self.retract()
            self.deployment = UNDEPLOYED
            self.completion = SUCCEEDED
            self.end_time = self.owner.sim.time
            if self.parent is not None:
                self.parent.child_succeeded(self)
            if self.observers is not None:
                for observer in self.observers:
                    observer.target_succeeded(self)
                    
    def fail(self):
        """Complete the action with a failure state. With the action pushed into the simulation 
        stack, the parent action and observers are warned of the action's failure."""
        with self.in_stack("F"):
            if self.deployment is UNDEPLOYED:
                raise ValueError("cannot fail() - action is undeployed")
            if self.deployment is DEPLOYED:
                self.retract()
            self.deployment = UNDEPLOYED
            self.completion = FAILED
            self.end_time = self.owner.sim.time
            if self.parent is not None:
                self.parent.child_failed(self)
            if self.observers is not None:
                for observer in self.observers:
                    observer.target_failed(self)
                    
    def cancel(self):
        """Cancel an ongoing action. This is a "soft method" which only retracts the action if it 
        is deployed, otherwise it doesn't do anything."""
        if self.deployment is DEPLOYED:
            self.retract()
            self.deployment = UNDEPLOYED
            self.completion = CANCELED
            self.end_time = self.owner.sim.time
            
    def undeployed(self): return self.deployment is UNDEPLOYED
    def deploying(self):  return self.deployment is DEPLOYING
    def deployed(self):   return self.deployment is DEPLOYED
    def succeeded(self):  return self.completion is SUCCEEDED
    def failed(self):     return self.completion is FAILED
    def canceled(self):   return self.completion is CANCELED
    # -----------------------------------------------------
    # Deployment methods
    def reset(self):
        """Subclasses should initialize any attributes they add on this method. reset() is called
        during start(), immediately before the deploy() method.""" 
        pass
        
    def deploy(self):
        """Subclasses should deploy the action in this method, that is, set it ready for 
        activation, e.g. for the Delay action, deploying is putting the delay into the 
        simulator's schedule.""" 
        pass
        
    def retract(self):
        """This is the opposite of deploy(). Here the action should remove itself from wherever
        it was placed during deploy()."""
        pass
        
    # -----------------------------------------------------
    # Operator methods
    def child_succeeded(self, child):
        """Method called by child actions to warn the parent action (an operator) of their 
        success and allow it to take action accordingly."""
        raise NotImplementedError()
        
    def child_failed(self, child):
        """Method called by child actions to warn the parent action (an operator) of their 
        failure and allow it to take action accordingly."""
        raise NotImplementedError()
        
    # -----------------------------------------------------
    # Observer methods
    def target_succeeded(self, target):
        """Called by a target (observed) action on all its observers when it succeeds."""
        raise NotImplementedError()
        
    def target_failed(self, target):
        """Called by a target (observed) action on all its observers when it fails."""
        raise NotImplementedError()
        

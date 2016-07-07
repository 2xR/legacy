from datetime import datetime
from random import Random
import time

from khronos.des.engine.clock import Clock
from khronos.des.engine.stack import Stack
from khronos.des.engine.schedule import Schedule
from khronos.des.components import Process, Thread
from khronos.des.primitives import Action, Delay, Chain
from khronos.utils import Namespace, Clock as CPUClock

class Simulation(object):
    """The Simulation class provides a data structure to record data about simulation 
    configuration parameters, metadata, and results."""
    def __init__(self, config=(), meta=()):
        self.config  = Namespace(config) # configuration parameters
        self.meta    = Namespace(meta)   # metadata, like date, cpu time taken, etc
        self.results = Namespace()       # result namespace
        
class Simulator(Process):
    """Simulation engine class. Simulator objects are responsible for the coordination of 
    simulation runs, activating the correct processes at the right times, managing the event 
    schedule, RNG, etc."""
    def __init__(self, name=None, members=(), **kwargs):
        Process.__init__(self, name, None, members, **kwargs)
        self.__rng = Random()
        self.__clock = Clock()
        self.__stack = Stack()
        self.__schedule = Schedule()
        self.__cpu = CPUClock()
        self.__pause = None
        self.__simulation = None
        
    # -----------------------------------------------------
    # Simulator properties --------------------------------
    @property
    def rng(self):
        return self.__rng
        
    @property
    def clock(self):
        return self.__clock
        
    @property
    def time(self):
        return self.__clock.value
        
    @property
    def stack(self):
        return self.__stack
        
    @property
    def schedule(self):
        return self.__schedule
        
    @property
    def cpu(self):
        return self.__cpu
        
    @property
    def simulation(self):
        return self.__simulation
        
    # -----------------------------------------------------
    # Control methods -------------------------------------
    def single_run(self, duration=None, seed=None):
        self.start(seed)
        self.run(duration)
        return self.stop()
        
    def multi_run(self, n, duration=None):
        return [self.single_run(duration) for _ in xrange(n)]
        
    def start(self, seed=None):
        if not self.running:
            if seed is None:
                seed = int(time.time() * 1000)
            self.__rng.seed(seed)
            self.__clock.clear()
            self.__stack.clear()
            self.__schedule.clear()
            self.__cpu.clear()
            self.__pause = None
            self.__simulation = Simulation({"seed": seed}, {"date": datetime.now()})
            with self.__cpu.tracking():
                self.rewind()
                self.__stack.instant("%s (initialization)" % (self.__clock.value,))
                Process.start(self)
                
    def stop(self):
        if self.running:
            with self.__cpu.tracking():
                self.__stack.instant("%s (finalization)" % (self.__clock.value,))
                Process.stop(self)
            self.__simulation.config.duration = self.__clock.value
            self.__simulation.meta.cpu = self.__cpu.total
        return self.__simulation
        
    def pause(self):
        self.__pause = "manual pause"
        
    def run(self, delta=None, until=None):
        """Simulate for a period of time specified by 'delta', or up to 'until'."""
        if not self.running:
            self.start()
        self.__cpu.start()
        self.__clock.limit(rel=delta, abs=until)
        while self.__pause is None:
            instant = self.__next_instant()
            if instant is None:
                break
            self.__run_instant(instant)
        if self.__pause is not None:
            self.__stack.message("Simulator paused: %s" % (self.__pause,))
            self.__pause = None
        self.__cpu.stop()
        
    def leap(self, n=1):
        """Run a number of simulation instants (default 1). An instant consists of a set of 
        events with the same date, so this method should go through 'n' different dates."""
        if not self.running:
            self.start()
        self.__cpu.start()
        self.__clock.limit(None)
        x = 0
        while self.__pause is None and x < n:
            x += 1
            instant = self.__next_instant()
            if instant is None:
                break
            self.__run_instant(instant)
        if self.__pause is not None:
            self.__stack.message("Simulator paused: %s" % (self.__pause,))
            self.__pause = None
        self.__cpu.stop()
        
    def step(self, n=1):
        """Run a number (default 1) of scheduled events (Delay objects). Note that each scheduled 
        event may trigger a number of other events in the same instant."""
        if not self.running:
            self.start()
        self.__cpu.start()
        self.__clock.limit(None)
        x = 0
        while self.__pause is None and x < n:
            instant = self.__next_instant()
            if instant is None:
                break
            self.__stack.instant(self.__clock.value)
            while len(instant) > 0 and self.__pause is None and x < n:
                x += 1
                _, delay = instant.pop()
                delay.finish()
        if self.__pause is not None:
            self.__stack.message("Simulator paused: %s" % (self.__pause,))
            self.__pause = None
        self.__cpu.stop()
        
    def until(self, action):
        """Run the simulation until a specified action activates (either succeed or fail). If 
        the action is bound, an observer is created. The given action is executed by a 
        StopperThread object, which pauses the simulation when the action activates."""
        StopperThread(self, action).start()
        self.run()
        
    def __next_instant(self):
        """Advance the calendar and clock to the next simulation instant, and return it. The 
        simulation run is paused if the end of the schedule or the time limit was reached."""
        try:
            instant, date = self.__schedule.advance()
        except IndexError:
            self.__pause = "no more scheduled events"
            return None
        else:
            if self.__clock.advance_to(date):
                return instant
            self.__pause = "clock limit reached"
            return None
            
    def __run_instant(self, instant):
        self.__stack.instant(self.__clock.value)
        while len(instant) > 0 and self.__pause is None:
            _, delay = instant.pop()
            delay.finish()
            
    # -----------------------------------------------------
    # Stack manipulation ----------------------------------
    def __push_action(action, self, activation_type):
        self.__stack.push(action, activation_type)
        
    def __pop_action(action, self):
        if action is not self.__stack.pop():
            raise Exception("mismatching actions on stack.pop() operation")
            
    Action.push_to  = __push_action
    Action.pop_from = __pop_action 
    # -----------------------------------------------------
    # Primitive deployment --------------------------------
    def __deploy_delay(delay):
        self = delay.owner.sim
        date = self.__clock.value + self.__clock.convert(delay.length)
        if date < self.__clock.value:
            raise ValueError("attempting to schedule delay to past date")
        self.__schedule.insert(delay, date, (delay.priority, self.__rng.random()))
        
    def __retract_delay(delay):
        self = delay.owner.sim
        self.__schedule.remove(delay)
        
    Delay.deploy     = __deploy_delay
    Delay.retract    = __retract_delay
    # -----------------------------------------------------
    # Miscellaneous methods -------------------------------
    def status(self):
        return "simtime=%s, cputime=%.3f" % (self.__clock.value, self.__cpu.total)
        
    def launch(self, target, start_fnc=None, who=None):
        """Launch a thread/process in the middle of a simulation run. A start function may be 
        specified just like in Thread.start(). If the 'who' argument is specified, the Launch 
        action is bound to that process, otherwise it is bound to the simulator by default."""
        target.sim = self
        launch = Launch(target, start_fnc)
        launch.bind(who if who is not None else self)
        self.__stack.push(launch, "L")
        target.start(start_fnc)
        self.__stack.pop()
        return target
        
class Launch(Action):
    """This dummy action type is used to print launch actions correctly to the stack trace."""
    def __init__(self, target, start_fnc):
        Action.__init__(self)
        self.target = target
        self.start_fnc = start_fnc
        
    def __info__(self):
        start_fnc_name = "initialize" if self.start_fnc is None else self.start_fnc.__name__
        return "%s - %s()" % (self.target, start_fnc_name)
        
class StopperThread(Thread):
    """A thread used by the simulator's until() method. It pauses the simulation when the given 
    condition is met, i.e., the action activates."""
    def constructor(self, condition):
        condition = Action.convert(condition)
        if condition.owner is not None:
            condition = condition.observe()
        self.condition = condition 
        
    @Chain
    def initialize(self):
        yield self.condition
        self.sim.pause()
        

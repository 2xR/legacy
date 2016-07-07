"""
This simulation model can be used to compare the simulation results 
of an M/M/1 FIFO queue to theoretical results given by queueing theory.
http://homepages.inf.ed.ac.uk/jeh/Simjava/queueing/mm1_q/mm1_q.html
"""

from khronos.des import Simulator, Process, Chain
from khronos.des.extra.components.queueing import FIFOQueue
from khronos.statistics import Tally, collect, sample

class Customer(Process):
    """A customer requiring service in the FIFO queue."""
    interarrival = 20
    servtime = 15
    response = Tally()
    
    @Chain
    def initialize(self):
        with collect.diff(self.sim.clock.get, self.response.collect):
            servtime = sample.nonnegative(self.sim.rng.expovariate, 1.0 / Customer.servtime)
            yield self.sim["queue"].put_request(self, servtime)
            
class FifoSim(Simulator):
    """Generates customers with exponentially distributed interarrival times."""
    @Chain
    def initialize(self):
        Customer.autoname_reset()
        Customer.response.clear()
        while True:
            yield sample.nonnegative(self.sim.rng.expovariate, 1.0 / Customer.interarrival)
            self.launch(Customer())
            
    def finalize(self):
        print "Response time:", Customer.response.mean()
        print "Queue size:", self["queue"].queue_size.wmean()
        print "Utilization:", self["queue"].utilization()
        
def main():
    sim = FifoSim("sim", members=[FIFOQueue("queue")])
    sim.stack.trace = False
    sim.single_run(100000.0)
    
# ---------------------------------------------------------
# Variable-duration simulation ----------------------------
from khronos.statistics import SteadyState

class AutoStopper(Process):
    """Pauses the simulation when performance indicators stabilize."""
    check_interval = 10
    
    @Chain
    def initialize(self):
        queue = self.sim["queue"]
        indicators = [SteadyState(amplitude=0.01, observations=100,
                                  function=Customer.response.mean),
                      SteadyState(amplitude=0.001, observations=100,
                                  function=queue.queue_size.wmean),
                      SteadyState(amplitude=0.1, observations=100,
                                  function=queue.utilization)]
        while not all([indicator.check() for indicator in indicators]):
            yield self.check_interval
        print "Pausing simulation at", self.sim.time
        self.sim.pause()
        
def main_stable():
    sim = FifoSim("sim", members=[FIFOQueue("queue"), AutoStopper("stopper")])
    sim.stack.trace = False
    sim.single_run()
    
if __name__ == "__main__":
    main_stable()
    
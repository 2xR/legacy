"""
This model is equivalent to the last model (bank12) of SimPy's "The bank" tutorial.
http://simpy.sourceforge.net/SimPyDocs/TheBank.html
"""

from khronos.des import Simulator, Process, Chain
from khronos.des.extra.components.resources import Resource
from khronos.statistics import Tally, sample, collect

class Source(Process):
    """Source generates customers randomly."""
    number = 50
    interval = 10.0
    
    def reset(self):
        Customer.queueing_time.clear()
        Customer.autoname_reset()
        
    @Chain
    def initialize(self):
        sim = self.sim       
        for _ in xrange(self.number):
            sim.launch(Customer())
            yield sample.nonnegative(sim.rng.expovariate, 1.0 / self.interval)
            
class Customer(Process):
    """Customer arrives, is served and leaves."""
    queueing_time = Tally()
    time_in_bank = 12.0 
    message = "waiting"
    
    def status(self):
        return self.message
        
    @Chain
    def initialize(self):
        sim = self.sim
        clerk = sim.members["clerk"]
        clerk.members.add(self)
        with collect.diff(sim.clock.get, Customer.queueing_time.collect):
            yield clerk.acquire()
        self.message = "getting service"
        yield sample.nonnegative(sim.rng.expovariate, 1.0 / self.time_in_bank)
        clerk.members.remove(self)
        clerk.release()
        
sim = Simulator(name="bank", members=[Source("src"), Resource("clerk", capacity=2)])

def main(trace=False):
    sim.stack.trace = trace
    for seed in [393939, 31555999, 777999555, 319999771]:
        sim.single_run(2000.0, seed=None)
        print "Average wait for %3d completions was %6.2f minutes." \
            % (Customer.queueing_time.count(), Customer.queueing_time.mean())  
            
if __name__ == "__main__":
    main()
    
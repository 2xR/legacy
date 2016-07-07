"""
Simulation model taken from http://www.ibm.com/developerworks/linux/library/l-simpy.html
Numerical results can be compared with SimPy's results shown in the web site.
"""

from khronos.des import Simulator, Process, Chain
from khronos.des.extra.components.resources import Resource
from khronos.statistics import Tally, collect, sample

AISLES = 5         # Number of open aisles
ITEMTIME = 0.1     # Time to ring up one item
AVGITEMS = 20      # Average number of items purchased
CLOSING = 60*12    # Minutes from store open to store close
AVGCUST = 1500     # Average number of daily customers
RUNS = 10          # Number of times to run the simulation

class Customer(Process):
    queueing_time = Tally()
    service_time = Tally()
    
    @Chain
    def initialize(self):
        sim = self.sim
        items = 1 + int(sample.nonnegative(sim.rng.expovariate, 1.0 / AVGITEMS))
        with collect.diff(sim.clock.get, Customer.queueing_time.collect):
            yield sim.members["aisle"].acquire()
        with collect.diff(sim.clock.get, Customer.service_time.collect):
            yield items * ITEMTIME
        sim.members["aisle"].release()
        
class SupermarketSim(Simulator):
    aisles = 1
    
    def reset(self):
        self.members.clear()
        self.members["aisle"] = Resource(capacity=self.aisles)
        Customer.autoname_reset()
        Customer.queueing_time.clear()
        Customer.service_time.clear()
        
    @Chain
    def initialize(self):
        while True:
            yield sample.nonnegative(self.rng.expovariate, float(AVGCUST) / CLOSING)
            self.launch(Customer(parent=self))
            
def main(trace=False):
    sim = SupermarketSim("supermarket")
    sim.stack.trace = trace
    for AISLES in (6, 5):
        sim.aisles = AISLES
        for _ in xrange(RUNS):
            sim.single_run(CLOSING)
            print "Waiting time average: %.1f (std dev %.1f, maximum %.1f)" \
                % (Customer.queueing_time.mean(), 
                   Customer.queueing_time.stddev(),
                   Customer.queueing_time.max())
        print 'AISLES:', AISLES, '  ITEM TIME:', ITEMTIME
        
if __name__ == "__main__":
    main()
    
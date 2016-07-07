"""
Simulation model taken from http://onlamp.com/pub/a/python/2003/02/27/simpy.html
Results are collected and plotted, and can be compared visually with SimPy's results.
"""

from khronos.des import Simulator, Process, Chain
from khronos.des.extra.components.resources import Resource
from khronos.statistics import TSeries, Plotter

class Customer(Process):
    """Represents customer requiring service."""
    customers_served = 0
    customers_happy = 0
    toomuch = 0.25
    
    def service_time(self):
        return 0.1 # hour (6 minutes)
        
    @Chain
    def initialize(self):
        arrive = self.sim.time
        yield self.sim["phone"].acquire()
        yield self.sim["staff"].acquire()
        wait = self.sim.time - arrive
        yield self.service_time()
        self.sim["staff"].release()
        self.sim["phone"].release()
        Customer.customers_served += 1
        Customer.customers_happy += 1 if wait < Customer.toomuch else 0
        
class CallCenterSim(Simulator):
    """Generates customer traffic and resets 'served' and 'happy' counters at initialization."""
    rate = 40.0 # clients per hour (arrival rate)
    
    def reset(self):
        Customer.autoname_reset()
        Customer.customers_served = 0
        Customer.customers_happy = 0
        
    @Chain
    def initialize(self):
        while True:
            self.launch(Customer())
            yield self.rng.expovariate(CallCenterSim.rate)
            
def main():
    for n in (3, 4, 5):
        print "n =", n
        sim = CallCenterSim("callcenter")
        sim.stack.trace = False
        sim["phone"] = Resource(capacity=n)
        sim["staff"] = Resource(capacity=n)
        for run in xrange(5):
            sim.single_run(6 * 24)
            happiness = float(Customer.customers_happy) / Customer.customers_served
            print "\trun %d, unhappiness = %.2f%%" % (run, 100.0 * (1.0 - happiness))
            
class Collector(Process):
    """Periodically collects customer happiness to a time series."""
    collect_interval = 0.5
    
    @Chain
    def initialize(self):
        self.stat = TSeries(storing=True, time_fnc=self.sim.clock.get, time_scale=24.0)
        happy = 1.0
        while True:
            if Customer.customers_served > 0:
                happy = float(Customer.customers_happy) / Customer.customers_served
            self.stat.collect(100.0 * (1.0 - happy)) 
            yield self.collect_interval
            
def main_collection():
    colors = ("red", "green", "blue", "yellow", "black")
    for n in (3, 4, 5):
        print "n =", n
        sim = CallCenterSim("callcenter")
        sim.stack.trace = False
        sim["phone"] = Resource(capacity=n)
        sim["staff"] = Resource(capacity=n)
        sim["collector"] = Collector()
        plotter = Plotter()
        axes = plotter.add_axes()
        for run in xrange(5):
            sim.single_run(6 * 24)
            sim["collector"].stat.run_chart(axes=axes, color=colors[run])
            happiness = float(Customer.customers_happy) / Customer.customers_served
            print "\trun %d, unhappiness = %.2f%%" % (run, 100.0 * (1.0 - happiness))
        axes.set_title("%d lines and staff" % (n,))
        axes.set_xlabel("Time (days)")
        axes.set_ylabel("Unhappy customers (%)")
        axes.set_ylim(0, 100)
        plotter.update()
        
if __name__ == "__main__":
    main_collection()
    raw_input(" <Press return to finish.> ")
    
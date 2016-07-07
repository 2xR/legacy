"""This example was taken from section 6.5 (page 387) of 'Computer architecture - a quantitative 
approach' 4th edition, by John L. Hennessy and David A. Patterson."""

from khronos.des import Simulator, Process, Chain, Poll
from khronos.statistics import Tally, TSeries, SteadyState, Plotter, sample
from khronos.utils import Checkable

class IORequest(object):
    def __init__(self, arrival):
        self.arrival = arrival
        self.service = None
        self.departure = None
        
    def queueing_time(self):
        return self.service - self.arrival
        
    def service_time(self):
        return self.departure - self.service
        
    def response_time(self):
        return self.departure - self.arrival
        
class RequestQueue(Process):
    def reset(self):
        self.queue = []
        self.size = Checkable(0)
        self.pending = TSeries(storing=True, time_fnc=self.sim.clock.get)
        self.qtime = Tally() # queueing time
        self.stime = Tally() # service time
        self.rtime = Tally() # response time
        
    def put(self, io_request):
        self.queue.append(io_request)
        self.size.set(len(self.queue))
        self.pending.collect(len(self.queue))
        
    def get(self):
        io_request = self.queue.pop(0)
        self.size.set(len(self.queue))
        self.pending.collect(len(self.queue))
        return io_request
        
    def collect(self, io_request):
        # Collect indicators about a departing request.
        self.qtime.collect(io_request.queueing_time())
        self.stime.collect(io_request.service_time())
        self.rtime.collect(io_request.response_time())
        
    def finalize(self):
        print "Mean queue size (weighted):", self.pending.wmean()
        print "Mean queueing time:", self.qtime.mean()
        print "Mean service time:", self.stime.mean()
        print "Mean responese time:", self.rtime.mean()
        self.plotter = Plotter()
        self.pending.run_chart(axes=self.plotter, label="Pending requests", legend=True)
        
class Disk(Process):
    mean_service_time = 0.02 # Mean service time for one IO request.
    
    def reset(self):
        self.state = TSeries(numeric=False, time_fnc=self.sim.clock.get)
        self.state.collect("Idle")
        
    @Chain
    def initialize(self):
        sim = self.sim
        queue = sim.members["Queue"]
        while True:
            if queue.size.get() == 0:
                self.state.collect("Idle")
                yield Poll.greater_than(0, queue.size)
                self.state.collect("Busy")
            io_request = queue.get()
            io_request.service = sim.time
            yield sample.nonnegative(sim.rng.expovariate, 1.0 / Disk.mean_service_time)
            io_request.departure = self.sim.time
            queue.collect(io_request)
            
    def finalize(self):
        queue = self.sim.members["Queue"]
        if queue.running:
            queue.stop()  # Make sure to finalize the queue before the disk.
        self.state.collect(self.state.last_value())
        self.state.pareto_chart(axes=queue.plotter, title=self.name)
        print self, "utilization:", self.state.wrel_frequency("Busy")
        
class RequestGenerator(Process):
    arrival_rate = 40.0 # Number of IO requests per second.
    
    @Chain
    def initialize(self):
        sim = self.sim
        queue = sim.members["Queue"]
        while True:
            yield sample.nonnegative(sim.rng.expovariate, RequestGenerator.arrival_rate)
            queue.put(IORequest(sim.time))
            
class AutoStopper(Process):
    @Chain
    def initialize(self):
        queue = self.sim.members["Queue"]
        steady = SteadyState(amplitude=0.001, observations=50)
        while True:
            if steady.check(queue.rtime.mean()):
                self.sim.pause()
                raise Chain.success()
            yield 1.0
            
sim = Simulator("sim", members=[Disk(), 
                                Disk(), 
                                RequestQueue("Queue"), 
                                RequestGenerator(), 
                                AutoStopper()])

if __name__ == "__main__":
    sim.stack.trace = False
    sim.single_run()
    raw_input(" <Press return to finish.> ")
    sim.members["Queue"].plotter.close()
    

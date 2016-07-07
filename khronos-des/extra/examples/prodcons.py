from khronos.des import Simulator, Process, Chain, Poll
from khronos.utils import Checkable
from khronos.statistics import Plotter, FTable, TSeries, Tally, collect

class Queue(Process):
    content = None
    
    def reset(self):
        self.content = []
        self.size = Checkable(0)
        self.size_tseries = TSeries(time_fnc=self.sim.clock.get, storing=True)
        self.size_tseries.collect(0)
        self.category_ftable = FTable()
        Consumer.waiting_time.clear()
        
    def status(self):
        return self.content
        
    def put(self, obj):
        self.content.append(obj)
        self.size.set(len(self.content))
        self.size_tseries.collect(len(self.content))
        self.category_ftable.collect(obj)
        
    def get(self):
        obj = self.content.pop(0)
        self.size.set(len(self.content))
        self.size_tseries.collect(len(self.content))
        return obj
        
    def finalize(self):
        p = self.plotter = Plotter(rows=1, cols=2)
        Consumer.waiting_time.histogram(axes=p, title="Consumer waiting time")
        self.category_ftable.pie_chart(axes=p, title="Production distribution")
        self.size_tseries.run_chart(axes=p, title="Queue size time series",
                                    label="Queue size", color="green", legend=True)

class Producer(Process):
    @Chain
    def initialize(self):
        queue = self.sim.members["Queue"]
        while True:
            yield self.sim.rng.gauss(10.0, 2.0)
            yield Poll.less_or_equal(20, queue.size)
            obj = self.sim.rng.choice("abcdefg")
            queue.put(obj)
            
class Consumer(Process):
    waiting_time = Tally()
    
    @Chain
    def initialize(self):
        queue = self.sim.members["Queue"]
        while True:
            with collect.diff(self.sim.clock.get, Consumer.waiting_time.collect):
                yield Poll.greater_than(0, queue.size)
            queue.get()
            yield self.sim.rng.expovariate(1.0 / 10.0)
            
sim = Simulator("prodcons", members=[Queue("Queue")] + 
                                    [Producer() for _ in xrange(5)] + 
                                    [Consumer() for _ in xrange(5)])

if __name__ == "__main__":
    import sys
    
    s = Simulator(members=[Queue("Queue")])
    s.stack.trace = False
    for x in xrange(10):
        s.members.add(Producer())
        s.members.add(Consumer())
    s.single_run(1000, seed=None if len(sys.argv) < 2 else sys.argv[1])
    raw_input(" <Press return to finish.> ")
    s.members["Queue"].plotter.close()
    
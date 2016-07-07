from khronos.des import Simulator, Process, Chain, Request, Action
from khronos.utils import Deque, Namespace, biased_choice, indent
from khronos.statistics import TSeries, sample
from contextlib import contextmanager

class History(object):
    def __init__(self, time_fnc):
        self.time_fnc = time_fnc
        self.content = []
        self.stack = [self.content]
        
    def __str__(self):
        return "\n".join(str(block) for block in self.content)
        
    @contextmanager
    def add(self, name, *data, **kwdata):
        new_block = HistoryBlock(name, self.time_fnc(), data, kwdata)
        self.stack[-1].append(new_block)
        self.stack.append(new_block.content)
        yield
        assert self.stack.pop() is new_block.content
        new_block.end = self.time_fnc()
        
class HistoryBlock(object):
    def __init__(self, name, start, data, kwdata):
        self.name = name
        self.start = start
        self.end = None
        self.data = data
        self.kwdata = kwdata
        self.content = []
        
    def __str__(self):
        data = ", ".join(str(item) for item in self.data)
        kwdata = ", ".join("%s=%s" % (key, value) for key, value in self.kwdata.iteritems())
        if len(data) > 0:
            if len(kwdata) > 0:
                data = data + ", " + kwdata
        else:
            data = kwdata
        lines = ["[%s, %s] :: %s(%s)" % (self.start, self.end, self.name, data)] 
        lines.extend(indent(str(block)) for block in self.content)
        return "\n".join(lines)
        
class Product(object):
    """Products should simply be defined as subclasses of Product, but they can be any class as 
    long as they supply the necessary 'route' and 'complexity' attributes."""
    route = []
    complexity = {}
    
class Lot(Process):
    def constructor(self, product, quantity):
        self.product = product
        self.quantity = quantity
        
    @Chain
    def initialize(self):
        self.history = History(time_fnc=self.sim.clock.get)
        with self.history.add("cycle", product=self.product, quantity=self.quantity):
            for op in self.product.route:
                yield self.sim.tree[op].process(self)
        print self, "finished"
        print self.history
        
class LotRelease(Process):
    products = []
    quantity = {}
    interval = None
    
    @Chain
    def initialize(self):
        rng = self.sim.rng
        while True:
            yield sample.nonnegative(rng.expovariate, 1.0 / self.interval)
            product = rng.choice(self.products)
            quantity = biased_choice(self.quantity.keys(), self.quantity.values(), rng)
            self.sim.launch(Lot(product=product, quantity=quantity), who=self)
            
class Queue(Deque):
    """A queue class with a blocking get() method implemented using the Request primitive."""
    def __init__(self, *args, **kwargs):
        Deque.__init__(self, *args, **kwargs)
        self.requests = []
        
    def append(self, lot):
        if len(self.requests) > 0:
            self.requests[0].succeed(lot)
        else:
            Deque.append(self, lot)
            
    def get(self):
        return Request.custom(None, self.add_request, self.requests.remove)
        
    def add_request(self, request):
        if len(self) > 0:
            request.succeed(self.popleft())
        else:
            self.requests.append(request)
            
class Operation(Process):
    queue = []
    
    def status(self):
        return [lot.name for lot in self.queue]
        
    def reset(self):
        self.queue = Queue()
        
    @Chain
    def process(self, lot):
        with lot.history.add(self.name):
            self.queue.append(lot)
            yield Action() # passivate the lot until process finishes
            
class Machine(Process):
    IDLE = "idle"
    BUSY = "busy"
    
    current = None
    state = TSeries()
    
    def status(self):
        return "(%s) %s" % (self.state.last_value, self.current)
        
    def reset(self):
        self.state = TSeries(numeric=False, storing=True, time_fnc=self.sim.clock.get)
        self.current = None
        
    @Chain
    def initialize(self):
        while True:
            self.state.collect(Machine.IDLE)
            self.current = None
            self.current = (yield self.parent.queue.get()).result
            #yield self.prepare()
            yield self.process()
            self.current.action.succeed()
            
    @Chain
    def process(self):
        with self.current.history.add("process", machine=self.path):
            self.state.collect(Machine.BUSY)
            yield self.current.quantity * self.current.product.complexity[self.parent.name]
            
    def finalize(self):
        self.state.repeat()
        print self.path, self.state.report()
        
# -----------------------------------------------
# Simple example --------------------------------
class P1(Product):
    route = ["pre-assembly", "assembly", "packing"]
    complexity = {"pre-assembly": 1.20,
                  "assembly": 0.80,
                  "packing": 1.10}
    
class P2(Product):
    route = ["pre-assembly", "assembly", "packing"]
    complexity = {"pre-assembly": 0.95,
                  "assembly": 1.25,
                  "packing": 0.95}
    
sim = Simulator()
tree = sim.tree
tree["pre-assembly"] = Operation(members=[Machine(x) for x in xrange(2)])
tree["assembly"] = Operation(members=[Machine(x) for x in xrange(2)])
tree["packing"] = Operation(members=[Machine(x) for x in xrange(2)])
tree["lr"] = LotRelease(interval=12000.0, products=[P1,P2], 
                        quantity={10000: 0.50, 20000: 0.30, 25000: 0.15, 30000: 0.05})

from khronos.des import Process, Simulator, Chain
from khronos.statistics import TSeries, sample
from khronos.utils import biased_choice
from utils import Buffer

# -----------------------------------------------
# Auxiliary data structures
class Route(object):
    def __init__(self, operations):
        self.operations = list(operations)
        self.successor = dict()
        for x in xrange(len(self.operations) - 1):
            self.successor[self.operations[x]] = self.operations[x + 1]
            
class Product(object):
    def __init__(self, name, route=(), complexity=()):
        self.name = name
        self.route = Route(route)
        self.complexity = dict(complexity)
        self.counter = 0
        
    def new_lot(self, quantity):
        self.counter += 1
        return Lot("%s#%d" % (self.name, self.counter), self, quantity)
        
class Lot(object):
    def __init__(self, id, product, quantity):
        self.id = id
        self.product = product
        self.quantity = quantity
        
    def __str__(self):
        return self.id
        
# -----------------------------------------------
# Component classes
class LotRelease(Process):
    def constructor(self, product, quantity, interval):
        self.product = product
        self.quantity = quantity
        self.interval = interval
        
    @Chain
    def initialize(self):
        rng = self.sim.rng
        product = self.product
        quantities = self.quantity.keys()
        biases = self.quantity.values()
        target = self.sim.tree[product.route.operations[0]].queue
        while True:
            yield sample.nonnegative(rng.expovariate, 1.0 / self.interval)
            target.append(self.product.new_lot(biased_choice(quantities, biases, rng)))
            
class Operation(Process):
    def constructor(self):
        self.members.extend([Process("workers"), Process("machines")])
        self.queue = Buffer()
        self.tasks = Buffer()
        
    def add_machine(self, machine):
        self.members["machines"].add(machine)
        machine.operation = self
        
    def add_worker(self, worker):
        self.members["workers"].add(worker)
        worker.operation = self
        
    def status(self):
        queue = [lot.id for lot in self.queue]
        tasks = [str(task) for task in self.tasks]
        return "\nQueue: %s\nTasks: %s" % (queue, tasks)
        
    def reset(self):
        self.queue = Buffer()
        self.tasks = Buffer()
        
class Machine(Process):
    IDLE = "idle"
    BUSY = "busy"
    
    def constructor(self):
        self.state = TSeries()
        self.current = None
        self.operation = None
        
    def status(self):
        return "(%s) %s" % (self.state.last_value, self.current)
        
    def reset(self):
        self.state = TSeries(numeric=False, time_fnc=self.sim.clock.get)
        self.current = None
        
    @Chain
    def initialize(self):
        self.state.collect(Machine.IDLE)
        while True:
            lot = (yield self.operation.queue.get()).result # block until a lot is available
            load = LoadTask(lot, self)
            self.operation.tasks.append(load)
            yield load.observe() # block until operator finishes loading
            yield self.process()
            unload = UnloadTask(self)
            self.operation.tasks.append(unload)
            yield unload.observe() # block until operator finishes loading
            
    @Chain
    def process(self):
        self.state.collect(Machine.BUSY)
        yield self.current.quantity * self.current.product.complexity[self.operation.path]
        self.state.collect(Machine.IDLE)
        
    def finalize(self):
        # repeat the last collected state to "close" the interval when ending a simulation
        self.state.repeat()
        
class Worker(Process):
    IDLE = "idle"
    BUSY = "busy"
    
    def constructor(self):
        self.state = TSeries()
        self.current = None
        self.operation = None
        
    def status(self):
        return "(%s) %s" % (self.state.last_value, self.current)
        
    def reset(self):
        self.state = TSeries(numeric=False, time_fnc=self.sim.clock.get)
        self.current = None
        
    @Chain
    def initialize(self):
        self.state.collect(Worker.IDLE)
        while True:
            self.current = (yield self.operation.tasks.get()).result
            self.state.collect(Worker.BUSY)
            yield self.current # block until task is completed
            self.state.collect(Worker.IDLE)
            self.current = None
            
    def finalize(self):
        # repeat the last collected state to "close" the interval when ending a simulation
        self.state.repeat()
        
@Chain
def LoadTask(lot, machine):
    assert machine.current is None
    yield 60.0
    machine.current = lot
    
@Chain
def UnloadTask(machine):
    assert machine.current is not None
    yield 60.0
    lot = machine.current
    next_operation = lot.product.route.successor.get(machine.operation.path)
    if next_operation is not None:
        machine.operation.tasks.append(DeliverTask(lot, machine.sim.tree[next_operation]))
    machine.current = None
    
@Chain
def DeliverTask(lot, operation):
    yield 60.0
    operation.queue.append(lot)
    
# -----------------------------------------------
# Simple example model
P1 = Product("P1", ["preassy", "assy", "packing"], {"preassy": 1.2, "assy": 0.8, "packing": 1.1})
P2 = Product("P2", ["preassy", "assy", "packing"], {"preassy": 0.9, "assy": 1.3, "packing": 1.0})

machines = {"preassy": 2, "assy": 2, "packing": 2}
workers = {"preassy": 1, "assy": 1, "packing": 1}

sim = Simulator()
for operation in ("preassy", "assy", "packing"):
    sim[operation] = op = Operation()
    for x in xrange(machines[operation]):
        op.add_machine(Machine(x))
    for x in xrange(workers[operation]):
        op.add_worker(Worker(x))
sim["lr1"] = LotRelease(interval=30000.0, product=P1, 
                        quantity={10000: 0.50, 20000: 0.30, 25000: 0.15, 30000: 0.05})
sim["lr2"] = LotRelease(interval=18000.0, product=P2, 
                        quantity={10000: 0.25, 20000: 0.30, 25000: 0.20, 30000: 0.25})

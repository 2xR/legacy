from khronos.des import Simulator, Process, Action, Delay, Poll, Chain, Renege
from khronos.des.extra.components.resources import Store
from khronos.statistics import TSeries, Plotter
from khronos.utils import Checkable

# ---------------------------------------------------------
# Component classes ---------------------------------------
class Fit4U(Simulator):
    """Simulator subclass. Automatically creates a 'orders' group with all orders as its members,  
    and a plotter that is used by the workstations to plot a Pareto chart. Additionally, at 
    finalization, the simulation results are computed and printed."""
    def reset(self):
        if "orders" not in self:
            self["orders"] = Process(initialize_priority=-1.0)
        self["orders"].clear()
        self["orders"].extend(self.orders)
        self.plotter = Plotter.dummy()
        
    def finalize(self):
        sections = [self[name] for name in ("cut", "sew", "assy")]
        total_quantity = sum(order.quantity for order in self.orders)
        total_workers = sum(section.initial_workers for section in sections)
        
        results = self.simulation.results
        results.makespan = max(order.finish for order in self.orders)
        results.setup = sum(section.state.wabs_frequency(SETUP) for section in sections)
        results.productivity = total_quantity / (results.makespan * total_workers)
        print "Results for", self.name
        for key, value in sorted(results.iteritems()):
            print "\t", key, "=", value
            
class Order(Process):
    """Configuration parameters:
        quantity :: int
        product :: Product
    """
    successor = {None: "cut",
                 "cut": "sew",
                 "sew": "assy",
                 "assy": None,
                 "bench": None}
    
    def status(self):
        return "%d x %s" % (self.quantity, self.product.name)
        
    @Chain
    def initialize(self):
        self.location = None
        while Order.successor[self.location] is not None:
            next = Order.successor[self.location]
            yield self.sim.tree["%s.queue" % (next,)].content.put(self)
            yield Action()
        self.finish = self.sim.time
        self.parent = None
        self.stop()
        
class WorkStation(Process):
    """Configuration parameters:
        initial_workers :: int
        throughput_fnc :: callable(int) -> float
        changeover :: {(from, to): float}
        setup :: {product: float}
    """
    state = TSeries()
    workers = Checkable(0)
    throughput = 0.0
    current = None
    initial_workers = 0
    changeover = {}
    setup = {}
    
    def set_workers(self, workers):
        """This method is used by the line balancer to adjust the number of workers in each  
        assembly line and/or the workbenches, and update their throughput."""
        self.throughput = self.throughput_fnc(workers)
        self.workers.set(workers)
        
    def throughput_fnc(self, workers):
        raise NotImplementedError()
        
    def status(self):
        return "%d workers (throughput=%f) - %s - %s" % \
        (self.workers.get(), self.throughput, self.state.last_value(), self.current)
        
    def reset(self):
        if "queue" not in self:
            self["queue"] = Store()
        self["queue"].content.clear()
        self.state = TSeries(storing=False, numeric=False, time_fnc=self.sim.clock.get)
        self.workers = Checkable(self.initial_workers)
        self.throughput = self.throughput_fnc(self.initial_workers)
        self.current = None
        self.previous = None
        
    @Chain
    def initialize(self):
        queue = self["queue"]
        while True:
            yield self.fetch(queue)
            yield self.prepare(self.current.product)
            yield self.process(self.current)
            self.previous = self.current.product
            self.current.action.succeed()
            self.current = None
            
    @Chain
    def fetch(self, queue):
        """Get the order with minimum preparation time and maximum process time from the queue."""
        self.state.collect(IDLE)
        if len(queue.content) == 0:
            self.current = (yield queue.content.get()).result
        else:
            best_score = None
            best_order = None
            for order in queue.content:
                changeover = self.changeover.get((self.previous, order.product), 0.0)
                setup      = self.setup.get(order.product, 0.0)
                ptime      = order.quantity * order.product.complexity[self.name]
                score      = (-(changeover + setup), +ptime)
                if score > best_score:
                    best_score = score
                    best_order = order
            queue.content.remove(best_order)
            self.current = best_order
        self.current.location = self.name
        
    @Chain
    def prepare(self, product):
        """Prepare the workstation for processing the specified product. This may include a 
        changeover if the product is different from the one previously processed, and a setup 
        time for preparing the machinery to start working."""
        self.state.collect(CHANGEOVER)
        yield self.changeover.get((self.previous, product), 0.0)
        self.state.collect(SETUP)
        yield self.setup.get(product, 0.0)
        
    @Chain
    def process(self, order):
        """Simulate the processing of 'order' with a possibly variable number of workers."""
        self.state.collect(BUSY)
        remaining = order.quantity
        while True:
            if self.workers.get() == 0:
                self.state.collect(NO_WORKERS)
                yield Poll.greater_than(0, self.workers)
                self.state.collect(BUSY)
            rate = self.throughput / order.product.complexity[self.name]
            process = Delay(remaining / rate)
            yield Renege(process, Poll.not_equal_to(self.workers.get(), self.workers))
            remaining -= process.elapsed_time * rate
            if process.succeeded():
                raise Chain.success()
                
    def finalize(self):
        self.state.collect(self.state.last_value())
        self.state.pareto_chart(axes=self.sim.plotter, title=self.name)
        
class AssemblyLine(WorkStation):
    def throughput_fnc(self, workers):
        return sum(max(0, 100 - 20 * x) for x in xrange(workers)) / 8.0
        
class WorkBench(WorkStation):
    def throughput_fnc(self, workers):
        return 30 * workers / 8.0
        
class Balancer(Process):
    """This component periodically checks a given list of target workstations and redistributes 
    available workers to them, trying to maximize the total throughput of the production plant."""  
    @Chain
    def initialize(self):
        yield 0.0
        sections = [self.sim.tree[section] for section in self.targets]
        total_workers = sum(section.initial_workers for section in sections)
        wip = WIP(sections)
        while sum(wip.itervalues()) > 0.0:
            assignment = self.assign(total_workers, sections, wip)
            #self.print_assignment(assignment)
            for section, workers in assignment.iteritems():
                section.set_workers(workers)
            yield self.update_interval
            wip = WIP(sections)
            
    def assign(self, total_workers, sections, wip):
        """This method computes a suitable assignment of workers to assembly lines. Workers are  
        assigned as follows: first assign the minimum required workers to each section, and then  
        assign the remaining workers one by one based on their contribution to throughput."""
        workers = dict((section, section.min_workers) for section in sections)
        total_workers -= sum(workers.itervalues())
        assert total_workers >= 0
        for _ in xrange(total_workers):
            best_score = None
            best_section = None
            for section in sections:
                delta_throughput = 0.0
                if section.state.last_value() not in (IDLE, CHANGEOVER, SETUP):
                    throughput0 = section.throughput_fnc(workers[section])
                    throughput1 = section.throughput_fnc(workers[section] + 1)
                    delta_throughput = throughput1 - throughput0
                score = (delta_throughput, wip[section])
                if score > best_score:
                    best_score = score
                    best_section = section
            workers[best_section] += 1
        return workers
        
    def print_assignment(self, assignment):
        """Print an assignment of workers to sections (used for debugging)."""
        print self.sim.time, "::", 
        for section in sorted(assignment, key=lambda s: s.name):
            print "%s: %d" % (section.name, assignment[section]),
        print ""
        
class Dispatcher(Process):
    """This component works similarly to the Balancer, but its job is to send small orders to the 
    workbenches. At each update, if the workbenches are idle, the order with maximum preparation 
    time per pair is selected and removed from the queue of the "cut" section, and sent to the  
    workbenches. Note that only small orders (quantity <= 20) are considered."""
    @Chain
    def initialize(self):
        yield Delay(0.0, priority=1.0)
        cut         = self.sim.tree["cut"]
        cut_queue   = self.sim.tree["cut.queue"]
        bench       = self.sim.tree["bench"]
        bench_queue = self.sim.tree["bench.queue"]
        while len(cut_queue.content) > 0:
            if bench.current is None:
                best_score = None
                best_order = None
                for order in cut_queue.content:
                    if order.quantity <= 20:
                        changeover = cut.changeover.get((cut.previous, order.product), 0.0)
                        setup      = cut.setup.get(order.product, 0.0)
                        score      = (changeover + setup) / order.quantity
                        if score > best_score:
                            best_score = score
                            best_order = order
                if best_order is not None:
                    cut_queue.content.remove(best_order)
                    yield bench_queue.content.put(best_order)
            yield Delay(self.update_interval, priority=1.0)
            
# ---------------------------------------------------------
# Support code --------------------------------------------
IDLE       = "idle"
CHANGEOVER = "changeover"
SETUP      = "setup"
BUSY       = "busy"
NO_WORKERS = "no workers"

class Product(object):
    """Auxiliary data structure which contains product name and complexity information."""
    def __init__(self, name, complexity=()):
        self.name = name
        self.complexity = dict(complexity)
        
def WIP(sections):
    """Compute per-section WIP, i.e., the sum of raw process time (qty * cpx, independent of 
    current throughput) of all queued and ongoing orders of the given sections."""
    ptime = lambda o, s: o.quantity * o.product.complexity[s.name]
    wip = {}
    for section in sections:
        wip[section] = sum(ptime(order, section) for order in section["queue"].content)
        if section.current is not None:
            wip[section] += ptime(section.current, section)
    return wip
    

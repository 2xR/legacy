"""
This model is inspired in Kounev's paper "J2EE performance and scalability: from measuring to 
predicting" in 2006. A model and a set of parameterizations are created, to reproduce those shown 
in the paper. Numeric results can be compared directly to the results shown in the paper.
"""

from khronos.des import Simulator, Process, Chain
from khronos.des.extra.components.queueing import FIFOQueue, PSQueue
from khronos.statistics import Tally, SteadyState, sample, collect, mean
from khronos.utils import Namespace, Reportable

class Transaction(Process):
    subtransactions = 1
    think_time = 0.0
    alive = False
    route = []
    location = "???"
    
    def status(self):
        return "@ %s (cycle %d)" % (self.location, self.cycles + 1)
        
    @Chain
    def initialize(self):
        sim = self.sim
        exponential = lambda mean: sample.nonnegative(sim.rng.expovariate, 1.0 / mean)
        servers = [sim.tree[srv] for srv, _ in self.route]
        stimes = [stime for _, stime in self.route]
        
        self.cycles = 0
        self.location = None
        self.alive = True
        while self.alive:
            current_stimes = [exponential(stime) for stime in stimes]
            with collect.diff(sim.clock.get, self.response.collect):
                for x in xrange(1, self.subtransactions + 1):
                    for server, stime in zip(servers, current_stimes):
                        self.location = server
                        yield server.put_request(self, stime / self.subtransactions)
                        self.location = None
                    yield self.subtransaction_finished(x)
            yield self.transaction_finished()
            self.cycles += 1
        self.parent = None
        
    @Chain
    def subtransaction_finished(self, x):
        raise Chain.success()
        
    @Chain
    def transaction_finished(self):
        yield sample.nonnegative(self.sim.rng.expovariate, 1.0 / self.think_time)
        
class Browse(Transaction):
    response = Tally()
    steady = SteadyState(amplitude=1.0, observations=50, function=response.mean)
    subtransactions = 17
    think_time = 5000.0
    
class Manage(Transaction):
    response = Tally()
    steady = SteadyState(amplitude=1.0, observations=50, function=response.mean)
    subtransactions = 5
    think_time = 5000.0
    
class Purchase(Transaction):
    response = Tally()
    steady = SteadyState(amplitude=1.0, observations=50, function=response.mean)
    subtransactions = 5
    think_time = 5000.0
    prob_large = 0.10
    
    @Chain
    def transaction_finished(self):
        if self.sim.rng.random() < self.prob_large:
            self.sim.launch(LargeOrder(parent=self.parent), who=self)
        yield sample.nonnegative(self.sim.rng.expovariate, 1.0 / self.think_time)
        
class WorkOrder(Transaction):
    response = Tally()
    steady = SteadyState(amplitude=1.0, observations=50, function=response.mean)
    subtransactions = 4
    subtrans_think = 333.0
    think_time = 10000.0
    
    @Chain
    def subtransaction_finished(self, x):
        if x < self.subtransactions:
            yield sample.nonnegative(self.sim.rng.expovariate, 1.0 / self.subtrans_think)
            
class LargeOrder(Transaction):
    response = Tally()
    steady = SteadyState(amplitude=1.0, observations=50, function=response.mean)
    
    @Chain
    def transaction_finished(self):
        self.alive = False
        raise Chain.success()
        
class RoundRobin(Process):
    """This component forwards transactions to its members in round-robin fashion."""
    index = 0
    
    def status(self):
        return "-> %d" % (self.index,)
        
    def reset(self):
        self.index = 0
        
    def put_request(self, process, servtime):
        result = self.members[self.index].put_request(process, servtime)
        self.index = (self.index + 1) % len(self.members)
        return result
        
class SPECj2004Sim(Simulator):
    def reset(self):
        # Transaction configuration and initialization 
        self.members.clear()
        config = self.config
        ttypes = (Browse, Purchase, Manage, WorkOrder, LargeOrder)
        self.tree["Tx"] = transactions = Process()
        for ttype in ttypes:
            ttype.response.clear()
            ttype.steady.clear()
            ttype.route = config.route[ttype.__name__]
            for x in xrange(config.clients[ttype.__name__]):
                transactions.members.add(ttype("%s%02d" % (ttype.__name__, x)))
        # Model construction
        self.tree["LB"] = PSQueue()
        self.tree["AS"] = RoundRobin(members=[PSQueue(x) for x in xrange(config.servers)])
        self.tree["DB"] = Process()
        self.tree["DB.cpu"] = RoundRobin(members=[PSQueue(x) for x in xrange(config.db_cpus)])
        self.tree["DB.disk"] = FIFOQueue()
        
    @Chain
    def initialize(self):
        ttypes = (Browse, Purchase, Manage, WorkOrder, LargeOrder)
        while True:
            yield 5000.0
            print self.time,
            if all([ttype.steady.check() for ttype in ttypes]):
                self.stop()
                raise Chain.success()
                
    def compute_results(self):
        ttypes = (Browse, Purchase, Manage, WorkOrder, LargeOrder)
        results = Namespace(txcount=Namespace(),
                            response=Namespace(),
                            throughput=Namespace(), 
                            utilization=Namespace())
        for ttype in ttypes:
            results.txcount[ttype.__name__]    = ttype.response.count()
            results.response[ttype.__name__]   = ttype.response.mean()
            results.throughput[ttype.__name__] = ttype.response.count() / (self.time / 1000.0)
        results.utilization.LB = self.tree["LB"].utilization()
        results.utilization.AS = mean([srv.utilization() for srv in self.tree["AS"].members])
        results.utilization.DB_cpu = mean([cpu.utilization() for cpu in self.tree["DB.cpu"].members])
        results.utilization.DB_disk = self.tree["DB.disk"].utilization()
        return results
        
    def finalize(self):
        print "\n"
        results = self.compute_results()
        self.simulation.results.update(results)
        ttypes = ("Browse", "Purchase", "Manage", "WorkOrder", "LargeOrder")
        items = [("Completed transactions", ""), 
                 [(ttype, results.txcount[ttype]) for ttype in ttypes], 
                 ("Throughput (transactions/sec)", ""), 
                 [(ttype, results.throughput[ttype]) for ttype in ttypes], 
                 ("Response time (ms)", ""), 
                 [(ttype, results.response[ttype]) for ttype in ttypes], 
                 ("Utilization (%)", ""), 
                 [("Load balancer",        results.utilization.LB), 
                  ("Application server",   results.utilization.AS), 
                  ("Database server  cpu", results.utilization.DB_cpu), 
                  ("Database server disk", results.utilization.DB_disk)]]
        print Reportable.report(items)
        
# ---------------------------------------------------------
# Model configurations ------------------------------------
normal_lb = Namespace(Browse = [("LB", 42.72), ("AS", 130.0), ("DB.cpu", 14.0), ("DB.disk", 5.0)],
                      Purchase = [("LB", 9.98), ("AS", 55.0), ("DB.cpu", 16.0), ("DB.disk", 8.0)],
                      Manage = [("LB", 9.93), ("AS", 59.0), ("DB.cpu", 19.0), ("DB.disk", 7.0)],
                      WorkOrder = [("AS", 34.0), ("DB.cpu", 24.0), ("DB.disk", 2.0)],
                      LargeOrder = [("AS", 92.0), ("DB.cpu", 34.0), ("DB.disk", 2.0)])
better_lb = Namespace(Browse = [("LB", 32.25), ("AS", 130.0), ("DB.cpu", 14.0), ("DB.disk", 5.0)],
                      Purchase = [("LB", 8.87), ("AS", 55.0), ("DB.cpu", 16.0), ("DB.disk", 8.0)],
                      Manage = [("LB", 8.56), ("AS", 59.0), ("DB.cpu", 19.0), ("DB.disk", 7.0)],
                      WorkOrder = [("AS", 34.0), ("DB.cpu", 24.0), ("DB.disk", 2.0)],
                      LargeOrder = [("AS", 92.0), ("DB.cpu", 34.0), ("DB.disk", 2.0)])

validation1 = Namespace(servers=2,
                        db_cpus=2,
                        route=normal_lb,
                        clients=Namespace(Browse     = 20,
                                          Purchase   = 10,
                                          Manage     = 10,
                                          WorkOrder  = 30,
                                          LargeOrder = 0))
validation2 = Namespace(servers=2,
                        db_cpus=2,
                        route=normal_lb,
                        clients=Namespace(Browse     = 40,
                                          Purchase   = 20,
                                          Manage     = 30,
                                          WorkOrder  = 50,
                                          LargeOrder = 0))
normal1 = Namespace(servers=4,
                    db_cpus=2,
                    route=normal_lb,
                    clients=Namespace(Browse     = 40,
                                      Purchase   = 16,
                                      Manage     = 16,
                                      WorkOrder  = 50,
                                      LargeOrder = 0)) 
normal2 = Namespace(servers=6,
                    db_cpus=2,
                    route=normal_lb,
                    clients=Namespace(Browse     = 40,
                                      Purchase   = 16,
                                      Manage     = 16,
                                      WorkOrder  = 50,
                                      LargeOrder = 0)) 
peak1 = Namespace(servers=6,
                  db_cpus=2,
                  route=normal_lb,
                  clients=Namespace(Browse     = 100,
                                    Purchase   = 26,
                                    Manage     = 26,
                                    WorkOrder  = 100,
                                    LargeOrder = 0)) 
peak2 = Namespace(servers=6,
                  db_cpus=2,
                  route=better_lb,
                  clients=Namespace(Browse     = 100,
                                    Purchase   = 26,
                                    Manage     = 26,
                                    WorkOrder  = 100,
                                    LargeOrder = 0)) 
heavy1 = Namespace(servers=8,
                   db_cpus=2,
                   route=better_lb,
                   clients=Namespace(Browse     = 150,
                                     Purchase   = 26,
                                     Manage     = 26,
                                     WorkOrder  = 100,
                                     LargeOrder = 0)) 
heavy2 = Namespace(servers=8,
                   db_cpus=2,
                   route=better_lb,
                   clients=Namespace(Browse     = 200,
                                     Purchase   = 26,
                                     Manage     = 26,
                                     WorkOrder  = 100,
                                     LargeOrder = 0))
scenario = Namespace(validation1=validation1,
                     validation2=validation2,
                     normal1=normal1,
                     normal2=normal2,
                     peak1=peak1,
                     peak2=peak2,
                     heavy1=heavy1,
                     heavy2=heavy2)
sim = SPECj2004Sim("sim", config=validation1)

if __name__ == "__main__":
    sim.stack.trace = False
    for name, config in sorted(scenario.iteritems()):
        print "_" * 60
        print "Configuration:", name
        sim.config = config
        sim.single_run(600000.0)
        print "_" * 60
        
"""Below is an alternative implementation of the Browse transaction type, just for educational 
purposes. Replacing the browse class with this one should yield the same simulation results."""
#class Browse(Process):
#    response = Tally()
#    steady = SteadyState(amplitude=1.0, observations=50, function=response.mean)   
#    subtransactions = 17
#    think_time = 5000.0
#    route = [("LB", 42.72), ("AS", 130.0), ("DB.cpu", 14.0), ("DB.disk", 5.0)]
#    @Chain
#    def initialize(self):
#        sim = self.sim
#        # Auxiliary function to generate exponentially distributed values
#        exponential = lambda mean: sample.nonnegative(sim.rng.expovariate, 1.0 / mean)
#        servtime = dict(Browse.route)
#        while True:
#            # Generate service times
#            lb_stime  = exponential(servtime["LB"])
#            as_stime  = exponential(servtime["AS"])
#            dbc_stime = exponential(servtime["DB.cpu"])
#            dbd_stime = exponential(servtime["DB.disk"])
#            # Go through the servers 17 times, and collect elapsed time
#            with collect.diff(sim.clock.get, Browse.response.collect):
#                for x in xrange(Browse.subtransactions):
#                    yield sim.tree["LB"].put_request(self, lb_stime / Browse.subtransactions)
#                    yield sim.tree["AS"].put_request(self, as_stime / Browse.subtransactions)
#                    yield sim.tree["DB.cpu"].put_request(self, dbc_stime / Browse.subtransactions)
#                    yield sim.tree["DB.disk"].put_request(self, dbd_stime / Browse.subtransactions)
#            # Wait before starting next browse transaction
#            yield exponential(Browse.think_time)
#            
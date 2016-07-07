from math import log

from khronos.des import Process, Chain, Delay, Action
from khronos.statistics import Tally, sample, collect
from khronos.utils import biased_choice

class Transaction(Process):
    location = None
    speed = 1.0
    
    def status(self):
        return "@ %s (%.02f%%)" % (self.location, self.speed * 100.0)
        
    @Chain
    def run(self):
        """This chain implements the execution of one complete transaction (many subtransactions),
        that is, the passage of all subtransactions that compose it through all the servers. 
        Response time is measured and recorded to a 'response' collector which is defined in 
        subclasses individually (one collector for each transaction type).
        Note that think time is not included in this chain, as it is not part of the execution of 
        the transaction. Instead, it is executed in the main chain, 'initialize()'."""
        # ---------------------------
        # Generation of service times
        SUT = self.sim["SUT"]
        #exponential = lambda mu: sample.nonnegative(self.sim.rng.expovariate, 1.0 / mu)
        def exponential(mu):
            if mu == 0.0:
                return 0.0
            return sample.nonnegative(self.sim.rng.expovariate, 1.0 / mu)
        servers = [SUT.tree[srv] for srv, _ in self.service_time]
        stimes = [exponential(stime) for _, stime in self.service_time]
        # ---------------------------
        self.processing = False
        self.location = None
        self.speed = 1.0
        with collect.diff(self.sim.clock.get, self.response.collect):
            for x in xrange(1, self.subtransactions + 1):
                for server, stime in zip(servers, stimes):
                    self.location = (yield server.acquire(self)).result
                    yield self.process(stime / self.subtransactions)
                    self.location.release(self)
                    self.location = None
                yield self.subtransaction_completed(x)
        yield self.transaction_completed()
        
    @Chain
    def process(self, remaining):
        self.processing = True
        while True:
            speed = self.speed
            delay = Delay(float(remaining) / speed)
            yield delay
            if delay.succeeded():
                break
            remaining -= delay.elapsed_time * speed # previous transaction speed
        self.processing = False
        self.speed = 1.0 # reset speed
        
    def set_speed(self, speed):
        self.speed = speed
        if self.processing:
            self.action.fail() # force recomputation of remaining time
            
    @Chain
    def subtransaction_completed(self, x):
        raise Chain.success()
        
    @Chain
    def transaction_completed(self):
        raise Chain.success()
        
class DealerTransaction(Transaction):
    type_map = dict() # Map of transaction type names to classes
    
    @classmethod
    def next_type(cls, rng):
        """Returns the type of the next dealer transaction, chosen based on the probabilities 
        specified by the 'mix' attribute."""
        ttype = biased_choice(cls.mix.keys(), cls.mix.values(), rng=rng)
        return {"Browse": Browse, "Purchase": Purchase, "Manage": Manage}[ttype]
        
    @Chain
    def initialize(self):
        rng = self.sim.rng
        t0 = self.sim.time
        yield self.run()
        t1 = self.sim.time
        yield max(0.0, self.cycle_time() - (t1 - t0))
        self.sim.launch(self.next_type(rng)(parent=self.parent), who=self)
        self.parent.remove(self)
        
    def cycle_time(self):
        """Randomly generate target cycle time for a transaction according to section 2.6.3 of 
        the 'Run and Reporting Rules' document."""
        return -log(self.sim.rng.random()) * 10000.0 # mean_CT = 10sec
        
class Browse(DealerTransaction):
    response = Tally()
    subtransactions = 17
    
class Manage(DealerTransaction):
    response = Tally()
    subtransactions = 5
    
class Purchase(DealerTransaction):
    response = Tally()
    subtransactions = 5
    
class WorkOrder(Transaction):
    response = Tally()
    subtransactions = 4
    production_time = 333.0
    cycle_time = 5000.0
    prob_large = 1.0 / 9.0
    
    @Chain
    def initialize(self):
        t0 = self.sim.time
        yield self.run()
        t1 = self.sim.time
        yield max(0.0, self.cycle_time - (t1 - t0))
        self.sim.launch(WorkOrder(parent=self.parent), who=self)
        self.parent.remove(self)
        
    @Chain
    def subtransaction_completed(self, x):
        if x < self.subtransactions:
            yield self.production_time
            
    @Chain
    def transaction_completed(self):
        if self.sim.rng.random() < self.prob_large:
            self.sim.launch(LargeOrder(parent=self.parent), who=self)
        raise Chain.success()
        
class LargeOrder(Transaction):
    response = Tally()
    subtransactions = 1
    
    @Chain
    def initialize(self):
        yield self.run()
        self.parent.remove(self)
        
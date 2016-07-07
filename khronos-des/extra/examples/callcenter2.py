"""
Scenario:
A call center runs around the clock. It has a number of agents online with different skills. Calls 
by clients with different questions arrive at an expected rate of callrate per minute (exponential 
distribution). An agent only deals with clients with questions in his competence areas. The number 
of agents online and their skills remain constant -- when an agent goes offline, he is replaced by 
one with the same skills.
The expected service time per question follows an exponential distribution.
Clients are impatient and renege if they don't get service within acceptable time.

Objectives:
    * Determine the waiting times of clients.
    * Determine the percentage of renegers.
    * Determine the utilization of agents.
"""

from khronos.des import Simulator, Process, Chain, Delay
from khronos.des.extra.components.resources import Store
from khronos.utils import Namespace, biased_choice
from khronos.statistics import FTable, Tally, TSeries, collect, sample

## Model components -----------------------------------------------------------
class CallGenerator(Process):
    """Necessary configuration parameters:
        needs :: [(need, prob)]
        call_rate :: float
        timeout :: float
    """
    def reset(self):
        Client.autoname_reset()
        Client.queueing_time.clear()
        Client.satisfaction.clear()
        
    @Chain
    def initialize(self):
        sim = self.sim
        needs = [need for need, _ in self.needs]
        probs = [prob for _, prob in self.needs]
        while True:
            yield sample.nonnegative(sim.rng.expovariate, self.call_rate)
            client = Client(timeout=self.timeout, need=biased_choice(needs, probs, rng=sim.rng))
            sim.launch(client)
            
    def finalize(self):
        results = self.sim.simulation.results
        results.renegers = Client.satisfaction.rel_frequency("reneged")
        results.queueing_time = Client.queueing_time.snapshot("mean", "var", "max")
        
class Client(Process):
    """Necessary configuration parameters:
        timeout :: float
        need :: str
    """
    queueing_time = Tally()
    satisfaction = FTable()
    
    @Chain
    def initialize(self):
        sim = self.sim
        queue = sim.members["queue"]
        yield queue.content.put(self)
        with collect.diff(sim.clock.get, Client.queueing_time.collect):
            timeout = Delay(self.timeout, priority=-1.0)
            yield timeout
        if timeout.succeeded():
            queue.content.remove(self)
            Client.satisfaction.collect("reneged")
        else:
            Client.satisfaction.collect("satisfied")
            
class Agent(Process):
    """Necessary configuration parameters:
        skills :: [skill]
        service_time :: {need: float}
    """
    client = None
    
    def status(self):
        if self.client is None:
            return "idle"
        return "%s (%s)" % (self.client.name, self.client.need)
        
    def reset(self):
        self.client = None
        self.state = TSeries(numeric=False, time_fnc=self.sim.clock.get)
        
    @Chain
    def initialize(self):
        sim = self.sim
        queue = sim.members["queue"]
        self.state.collect("idle")
        while True:
            self.state.collect("idle")
            self.client = (yield queue.content.get(filter=self.can_answer)).result
            yield 0.0
            self.client.action.fail() # cause the timeout to fail
            self.state.collect("busy")
            yield self.service_time[self.client.need]
            self.client = None
            
    def finalize(self):
        results = self.sim.simulation.results
        if "utilization" not in results:
            results.utilization = Namespace()
        self.state.collect("idle" if self.client is None else "busy")
        results.utilization[self.path] = self.state.wrel_frequency("busy")
        
    def can_answer(self, client):
        # filter function for Store.content.get()
        return client.need in self.skills
        
class CallCenterSim(Simulator):
    """Necessary configuration parameters:
        needs :: [str]
        timeout :: float
        call_rate :: float
        skillsets :: [(count, [skill])]
        service_time :: {need: float}
    """
    def reset(self):
        self.members.clear()
        self.members["queue"] = Store()
        self.members["generator"] = CallGenerator(needs=self.needs, 
                                                  timeout=self.timeout, 
                                                  call_rate=self.call_rate)
        self.members["agents"] = agents = Process()
        Agent.autoname_reset()
        for count, skills in self.skillsets:
            agents.members["+".join(skills)] = group = Process()
            for x in xrange(count):
                group.members.add(Agent(name=x, skills=skills, 
                                        service_time=self.service_time))
                
## Configuration Parameters ---------------------------------------------------
config = Namespace(needs=[("loan", 0.1), 
                          ("insurance", 0.1),
                          ("credit card", 0.3),
                          ("other", 0.5)],
                   timeout=0.5,
                   call_rate=7.0 / 10.0,
                   skillsets=[(1, ["loan"]),
                              (2, ["loan","credit card"]),
                              (2, ["insurance"]),
                              (2, ["insurance","other"])],
                   service_time={"loan": 3.0,
                                 "insurance": 4.0, 
                                 "credit card": 2.0,
                                 "other": 3.0})
sim = CallCenterSim(name="SimCityBank", **config)
sim.stack.trace_width = 110

if __name__ == "__main__":
    from pprint import pprint
    
    sim.stack.trace = False
    for sim.timeout in (0.5, 1.0, 2.0):
        sim.single_run(10 * 24 * 60.0)
        print "Timeout:", sim.timeout
        pprint(sim.simulation.results)
        
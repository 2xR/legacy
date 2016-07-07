from khronos.des import Simulator, Process, Chain, Request, Unless, Action
from khronos.statistics import FTable, Tally, TSeries, sample, collect, mean
from khronos.utils import Deque, Call

class CustomerRequest(Request):
    """A request which blocks a customer until a server is available."""  
    def constructor(self, queue):
        self.queue = queue
        
    def deploy(self):
        self.queue._add_request(self)
        
    def retract(self):
        self.queue._drop_request(self)
        
class Queue(Process):
    customers = []
    def status(self):
        return "\n".join(customer.name for customer in self.customers)
        
    def reset(self):
        self.customer_requests = Deque()
        self.idle_servers = Deque()
        self.size = TSeries(time_fnc=self.sim.clock.get)
        
    def wait_for_server(self):
        """Called by a customer to enter the queue for a server."""
        return CustomerRequest(self)
        
    def _add_request(self, request):
        if len(self.idle_servers) > 0:
            request.succeed(self.idle_servers.popleft())
        else:
            self.customer_requests.append(request)
            self.size.collect(len(self.customer_requests))
            
    def _drop_request(self, request):
        self.customer_requests.remove(request)
        self.size.collect(len(self.customer_requests))
        
    def idle(self, server):
        """Called by a server after being released by a customer."""
        if len(self.customer_requests) > 0:
            self.customer_requests[0].succeed(server)
        else:
            self.idle_servers.append(server)
            
    def finalize(self):
        self.size.collect(self.size.last_value)
        
class Server(Process):
    speed = 1.0
    customer = None
    def status(self):
        return self.customer
        
    def reset(self):
        self.state = TSeries(numeric=False, time_fnc=self.sim.clock.get)
        self.customer = None
        self.pending = []
        
    #@Chain
    def initialize(self):
        while True:
            self.customer = None
            self.state.collect("idle")
            self.customer, service_time = (yield self.sim.queue.idle(self)).result
            self.state.collect("busy")
            
    def finalize(self):
        self.state.collect(self.state.last_value)
        
    def serve(self, customer, service_time):
        inactive = bool(len(self.pending) == 0) 
        service = self._serve(customer, service_time)
        self.pending.append(service)
        if inactive:
            self.action.succeed()
        return service.observe()
        
    #@Chain
    def _serve(self, customer, service_time):
        self.customer = customer
        yield service_time / self.speed
        self.customer = None
        
class Teller(Server):
    speed = 1.00
    
class ATM(Server):
    speed = 0.75
    
class Customer(Process):
    """Bank customer arrive and get in line at the queue, waiting until a server is available, or 
    leaving the bank unsatisfied if their waiting time reaches a maximum 'patience' threshold. If 
    they get a server, the hold it for some time (service time) and finally leave the bank."""
    queueing_time = Tally()
    service_time = Tally()
    satisfaction = FTable()
    #@Chain
    def go(self, service_time, patience):
        with collect.diff(self.sim.clock.get, Customer.queueing_time.collect):
            request = self.sim.queue.wait_for_server()
            yield Unless(patience, request)
        if request.succeeded():
            with collect.diff(self.sim.clock.get, Customer.service_time.collect):
                server = request.result
                yield server.serve(self, service_time)
            Customer.satisfaction.collect("satisfied")
        else:
            Customer.satisfaction.collect("unsatisfied")
            
class Bank(Simulator):
    """Simulation model of a bank with tellers and ATMs. Customers arrive randomly at the bank
    with exponential inter-arrival time distribution, and Gaussian (normal) service time 
    distribution. The customers also have a normally distributed maximum waiting time. A customer 
    leaves the bank unsatisfied if he does not get service before the maximum waiting time is 
    reached.""" 
    interarrival_mean = 2.0
    service_time_mean = 5.0
    service_time_stddev = 1.0
    patience_mean = 10.0
    patience_stddev = 5.0
    servers = {Teller: 2, ATM: 1}
    
    def reset(self):
        self.members.clear()
        self.queue = Queue(name="Queue", parent=self)
        self.serverlist = []
        for srv_type, qty in self.servers.iteritems():
            for x in xrange(qty):
                server = srv_type(name="%s%d" % (srv_type.__name__, x), parent=self)
                self.serverlist.append(server)
        Customer.queueing_time.clear()
        Customer.service_time.clear()
        Customer.satisfaction.clear()
        
    #@Chain
    def initialize(self):
        customers = 0
        while True:
            yield sample.nonnegative(self.rng.expovariate, 1.0 / self.interarrival_mean)
            service_time = sample.nonnegative(self.rng.gauss, 
                                              self.service_time_mean, 
                                              self.service_time_stddev)
            patience = sample.nonnegative(self.rng.gauss,
                                          self.patience_mean,
                                          self.patience_stddev)
            customer = Customer(name="Customer%d" % (customers,))
            self.launch(customer, start_fnc=Call(customer.go, service_time, patience))
            customers += 1
            
sim = Bank("KhronosBank")
scenarios = [dict(scenario_name="1 Teller, 1 ATM",
                  run_chart_color="green",
                  interarrival_mean = 2.0,
                  service_time_mean = 5.0,
                  service_time_stddev = 1.0,
                  patience_mean = 10.0,
                  patience_stddev = 5.0,
                  servers = {Teller: 1, ATM: 1}),
             dict(scenario_name="2 Tellers, 1 ATM",
                  run_chart_color="blue",
                  interarrival_mean = 2.0,
                  service_time_mean = 5.0,
                  service_time_stddev = 1.0,
                  patience_mean = 10.0,
                  patience_stddev = 5.0,
                  servers = {Teller: 2, ATM: 1})]

def main(trace=False):
    fmt = "%20s: %s"
    sim.stack.trace = trace
    for scenario in scenarios:
        print "=" * 100
        print "Simulation parameters"
        for key, value in sorted(scenario.iteritems()):
            print "\t", fmt % (key, value)
        print "Running...",
        sim.__dict__.update(scenario)
        sim.single_run(60.0*24.0*31.0)
        print "finished"
        print "-" * 100
        print fmt % ("Total customers", Customer.satisfaction.total()) 
        print fmt % ("Unhappy customers", "%d (%.2f%%)" % 
                     (Customer.satisfaction.abs_freq("unsatisfied"),
                      Customer.satisfaction.rel_freq("unsatisfied") * 100.0))
        print fmt % ("Queue size mean", sim.queue.size.wmean())
        print fmt % ("Queue size var", sim.queue.size.wvar())
        print fmt % ("Queueing time mean", Customer.queueing_time.mean())
        print fmt % ("Queueing time var", Customer.queueing_time.var())
        print fmt % ("Service time mean", Customer.service_time.mean())
        print fmt % ("Service time var", Customer.service_time.var())
        utilization = mean([srv.state.wftable.rel_freq("busy") for srv in sim.serverlist])
        print fmt % ("Server utilization", utilization)
        axes = sim.queue.size.run_chart(color=sim.run_chart_color)
        axes.set_title(sim.scenario_name)
        axes.set_xlabel("Time (minutes)")
        axes.set_ylabel("Queue size")
        axes.figure.plotter.update()
        raw_input("Please press <return> to continue")
        #axes.figure.plotter.save(sim.scenario_name + ".pdf")
        axes.figure.plotter.close()
    print "Finished"
    
if __name__ == "__main__":
    main()
    
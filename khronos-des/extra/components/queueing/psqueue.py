from khronos.des import Process, Chain, Action, Request, Delay, Poll
from khronos.statistics import TSeries
from khronos.utils import Checkable

class PSQueue(Process):
    """Single-server processor sharing queue. This is used to represent how processes or threads 
    run in time-sharing mode in modern operating systems."""
    remaining = {}  # {request: remaining_servtime}
    
    def status(self):
        lines = ["%d requests" % (len(self.remaining),)]
        for request, remaining in self.remaining.iteritems():
            lines.append("%s (remaining=%f)" % (request.owner.name, remaining))
        return "\n".join(lines)
        
    def reset(self):
        self.remaining = {}
        self.ongoing = Checkable(0)
        self.state = TSeries(numeric=False, time_fnc=self.sim.clock.get)
        self.finishing = False
        self.start_time = None
        
    @Chain
    def initialize(self):
        while True:
            if len(self.remaining) == 0:
                self.state.collect("Idle")
                yield Poll.greater_than(0, self.ongoing)
                self.state.collect("Busy")
            self.start_time = self.sim.time
            nprocs = len(self.remaining)
            delay = Delay(min(self.remaining.itervalues()) * nprocs)
            yield delay
            self.update()
            if delay.failed():
                # Interrupted by put_request(), wait until it exits
                yield Action()
                
    def finalize(self):
        self.state.collect("Idle" if len(self.remaining) == 0 else "Busy")
        
    def put_request(self, process, servtime):
        request = Request(servtime)
        request.bind(process)
        interrupted = False
        if len(self.remaining) > 0 and not self.finishing:
            self.action.fail()
            interrupted = True
        self.remaining[request] = servtime
        self.ongoing.set(len(self.remaining))
        if interrupted:
            self.action.succeed()
        return request
        
    def update(self):
        # Update remaining service times and check for finished requests.
        nprocs = len(self.remaining)
        elapsed = (self.sim.time - self.start_time) / nprocs
        finished = []
        for request, remaining in self.remaining.iteritems():
            # This is required because of damn floating point arithmetic errors...
            if remaining - elapsed < 1e-6: 
                finished.append(request)
            else:
                self.remaining[request] = remaining - elapsed
        # Remove finished requests.
        if len(finished) > 0:
            self.finishing = True
            for request in finished:
                del self.remaining[request]
                request.fulfill()
            self.ongoing.set(len(self.remaining))
            self.finishing = False
            
    def utilization(self):
        return self.state.wrel_frequency("Busy") * 100.0
        
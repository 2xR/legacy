from khronos.des import Process, Chain, Request, Poll
from khronos.statistics import TSeries
from khronos.utils import Checkable, fit

class FIFOQueue(Process):
    """Single-server FIFO queue."""
    current = None
    queue = []
    
    def status(self):
        if self.current is not None:
            queue = fit(str([request.owner.name for request in self.queue]), 60)
            return "%s %s - %d queued customers %s" % (self.current.owner.name,
                                                       self.current.data,
                                                       len(self.queue), queue)
        return "[]"
        
    def reset(self):
        self.current = None
        self.queue = []
        self.queued = Checkable(0)
        self.queue_size = TSeries(time_fnc=self.sim.clock.get)
        self.state = TSeries(numeric=False, time_fnc=self.sim.clock.get)
        
    @Chain
    def initialize(self):
        self.queue_size.collect(0)
        while True:
            if len(self.queue) == 0:
                self.state.collect("Idle")
                yield Poll.greater_than(0, self.queued)
                self.state.collect("Busy")
            self.current = request = self.__popleft()
            yield request.data
            self.current = None
            request.fulfill()
            
    def finalize(self):
        self.state.collect("Idle" if self.current is None else "Busy")
        
    def put_request(self, process, servtime):
        request = Request(servtime)
        request.bind(process)
        self.__append(request)
        return request
        
    def __append(self, request):
        self.queue.append(request)
        self.queue_size.collect(len(self.queue))
        self.queued.set(len(self.queue))
        
    def __popleft(self):
        request = self.queue.pop(0)
        self.queue_size.collect(len(self.queue))
        self.queued.set(len(self.queue))
        return request
        
    def utilization(self):
        return self.state.wrel_frequency("Busy") * 100.0
        

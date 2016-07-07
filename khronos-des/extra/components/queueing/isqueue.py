from khronos.des import Process, Chain

class ISQueue(Process):
    """The IS queue (infinite server) merely represents a delay in a process' activity."""
    count = 0
    
    def status(self):
        return "%s customers" % (self.count,)
        
    def reset(self):
        self.count = 0
        
    @Chain
    def put_request(self, process, servtime):
        self.count += 1
        yield servtime
        self.count -= 1
        

from khronos.des import Process, Chain, Action
from khronos.statistics import SteadyState, TSeries, mean 
from khronos.utils import INF, Deque

class CPUBalancer(Process):
    """Sends the next request to the cpu currently running less processes."""
    def acquire(self, client):
        min_load = INF
        min_cpus = None
        for cpu in self.members:
            if len(cpu.clients) < min_load:
                min_cpus = [cpu]
                min_load = len(cpu.clients)
            elif len(cpu.clients) == min_load:
                min_cpus.append(cpu)
        return self.sim.rng.choice(min_cpus).acquire(client)
        
    def utilization(self):
        return mean([rsc.utilization() for rsc in self])
        
class PhysicalCPU(Process):
    clients = []
    speed = 1.0
    
    def status(self):
        if len(self.clients) == 0:
            return "idle"
        client_speed = 100.0 / len(self.clients) * self.speed
        lines = ["%d clients (%.02f%% to each)" % (len(self.clients), client_speed)]
        lines.extend(client.path for client in self.clients)
        return "\n".join(lines)
        
    def reset(self):
        self.state = TSeries(numeric=False, time_fnc=self.sim.clock.get)
        self.state.collect("Idle")
        self.clients = set()
        
    def finalize(self):
        self.state.collect("Idle" if len(self.clients) == 0 else "Busy")
        
    @Chain
    def acquire(self, client):
        yield Chain.result(self)
        if len(self.clients) == 0:
            self.state.collect("Busy")
        self.clients.add(client)
        self.update()
        
    def release(self, client):
        self.clients.remove(client)
        if len(self.clients) == 0:
            self.state.collect("Idle")
        else:
            self.update()
            
    def update(self):
        if len(self.clients) > 0:
            client_speed = self.speed / len(self.clients) 
            for client in self.clients:
                client.set_speed(client_speed)
                
    def utilization(self):
        return self.state.wrel_frequency("Busy") * 100.0
        
class VirtualCPU(PhysicalCPU):
    pCPU         = None # target for acquire() requests (may be a group of cpus)
    current_pCPU = None # pCPU where the vCPU is currently running
    
    def status(self):
        if len(self.clients) == 0:
            return "idle"
        client_speed = 100.0 / len(self.clients) * self.speed
        lines = ["%d clients (%.02f%% to each, total %.02f%% from %s)" % 
                 (len(self.clients), client_speed, self.speed * 100.0, self.current_pCPU)]
        lines.extend(client.path for client in self.clients)
        return "\n".join(lines)
        
    def reset(self):
        PhysicalCPU.reset(self)
        self.pCPU_utz = TSeries(time_fnc=self.sim.clock.get)
        self.pCPU_utz.collect(0.0)
        
    def finalize(self):
        PhysicalCPU.reset(self)
        self.pCPU_utz.collect(0.0)
        
    @Chain
    def acquire(self, client):
        yield Chain.result(self)
        if len(self.clients) == 0:
            self.current_pCPU = (yield self.pCPU.acquire(self)).result
        yield PhysicalCPU.acquire(self, client)
        
    def release(self, client):
        PhysicalCPU.release(self, client)
        if len(self.clients) == 0:
            self.current_pCPU.release(self)
            self.current_pCPU = None
            self.pCPU_utz.collect(0.0)
            
    def set_speed(self, speed):
        self.pCPU_utz.collect(speed)
        self.speed = speed
        self.update()
        
class DiskFIFO(Process):
    """A first-in-first-out disk."""
    current = None
    
    def status(self):
        if self.current is None:
            return "idle"
        lines = ["%s (%d queued)" % (self.current, len(self.queue))]
        lines.extend(client.path for client in self.queue)
        return "\n".join(lines)
        
    def reset(self):
        self.state = TSeries(numeric=False, time_fnc=self.sim.clock.get)
        self.state.collect("Idle")
        self.current = None
        self.queue = Deque()
        
    def finalize(self):
        self.state.collect("Idle" if self.current is None else "Busy")
        
    @Chain
    def acquire(self, client):
        yield Chain.result(self)
        if self.current is None:
            self.current = client
            self.state.collect("Busy")
            raise Chain.success()
        self.queue.append(client)
        yield Action() # suspend until activated by release()
        
    def release(self, client):
        assert client is self.current
        if len(self.queue) > 0:
            self.current = self.queue.popleft()
            self.current.action.succeed() # activate next in line
        else:
            self.current = None
            self.state.collect("Idle")
            
    def utilization(self):
        return self.state.wrel_frequency("Busy") * 100.0
        
class DiskDelay(Process):
    """A 'disk' which merely represents a fixed delay to transactions. To use it instead of a 
    DiskFIFO, simply change the import statement, for example, as follows
        from resources import DiskFIFO as Disk
    becomes
        from resources import DiskDelay as Disk
    This way the rest of the source file can remain unchanged."""
    @Chain
    def acquire(self, client):
        yield Chain.result(self)
        client.set_speed(1.0)
        
    def release(self, client):
        pass
        
    def utilization(self):
        return -100.0
        
class AutoStop(Process):
    """Automatically stops the simulation when the steady state conditions have been met."""
    amplitude = 2.0
    observations = 100
    period = 5000.0
    
    @Chain
    def initialize(self):
        steady = [SteadyState(amplitude=self.amplitude, 
                              observations=self.observations, 
                              function=ttype.response.mean) for ttype in self.ttypes]
        while True:
            yield self.period
            print self.sim.time
            if all([s.check() for s in steady]):
                print "*** Steady state condition verified at", self.sim.time
                self.sim.stop()
                raise Chain.success()
                
from khronos.des import Simulator, Thread, Process, Chain
from khronos.statistics import TSeries, Plotter

class Virus(Process):
    initial_population = 10
    maximum_population = 5000
    lifespan_mean = 10.0
    lifespan_stddev = 1.0
    replication_rate = 0.2
    
    @Chain
    def initialize(self):
        sim = self.sim
        death = sim.time + sim.rng.gauss(Virus.lifespan_mean, Virus.lifespan_stddev)
        replication_interval = sim.rng.expovariate(Virus.replication_rate)
        while sim.time + replication_interval < death:
            yield replication_interval
            Launcher(sim, origin=self, target=Virus(), delay=2).start()
            if len(sim.members) > Virus.maximum_population:
                sim.pause()
            replication_interval = sim.rng.expovariate(Virus.replication_rate)
        yield death - sim.time
        self.parent = None
        self.sim.count.collect(len(sim.members))
        
class Launcher(Thread):
    @Chain
    def initialize(self):
        yield self.delay
        self.target.parent = self.sim
        self.sim.launch(self.target, who=self.origin)
        
class VirusSim(Simulator):
    def reset(self):
        self.clock.precision = 0.5
        self.members.clear()
        Virus.autoname_reset()
        for _ in xrange(Virus.initial_population):
            self.members.add(Virus())
        self.count = TSeries(storing=True, time_fnc=self.clock.get)
        self.count.collect(len(self.members))
        
    @Chain
    def initialize(self):
        # Print time if trace is disabled.
        if not self.stack.trace:
            while True:
                print "%10.6f: %d viruses" % (self.time, len(self.members)) 
                yield 10
                
    def finalize(self):
        axes = self.count.run_chart(label="Registered growth", 
                                    title="Virus population", 
                                    legend=True)
        self.plotter = axes.figure.plotter
        print "\n" + self.count.report()
        
if __name__ == "__main__":
    s = VirusSim()
    s.stack.trace = False
    s.single_run()
    raw_input(" <Press return to finish.> ")
    s.plotter.close()
    

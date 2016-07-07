from multiprocessing import Manager, Pool, cpu_count, current_process

#    def split(self, parts=2):
#        parts = []
#        n = len(self.instances)
#        for x in xrange(parts):
#            parts.append(Experiment(self.instances[x / parts: (x+1) / parts])
            
class ParallelExperiment(Experiment):
    def setup(self, processes_per_cpu=1):
        self.pool = Pool(int(processes=processes_per_cpu * cpu_count()))
        self.manager = Manager()
        self.results = self.manager.dict() 
        print "Starting experiment (%d worker processes)..." % (len(self.pool._pool),)
        
    def run(self, *args, **kwargs):
        print "Parameters:"
        print "\t", args
        print "\t", kwargs
        for instance in self.instances:
            for method in self.methods:
                all_args = (method, instance, self.results) + args
                self.pool.apply_async(_parallel_subrun, all_args, kwargs)
        self.pool.close()
        self.pool.join()
        
def _parallel_subrun(method, instance, results, *args, **kwargs):
    pid = current_process().pid 
    print "[%10s] Starting %s on instance %s" % (pid, method.__class__.__name__, instance)
    method.execute(instance, results, *args, **kwargs)
    print "[%10s] Completed %s on instance %s" % (pid, method.__class__.__name__, instance)
    
Experiment.parallel = ParallelExperiment


# EXAMPLE CODE FOR PARALLEL EXPERIMENT BELOW
#class Foo(Method):
#    def __init__(self, name):
#        self.name = name
#        
#    def setup(self, instance):
#        print self.name, "setup(", self, instance, ")"
#        self.instance = instance
#        
#    def run(self, *args, **kwargs):
#        print self.name, args
#        print self.name, kwargs
#        self.result = self.instance, args, kwargs
#        
#    def finalize(self, results):
#        print self.name, "finalize(", results, ")"
#        l = results.get(self.name, [])
#        l.append(self.result)
#        results[self.name] = l
#        
#methods = [Foo(x) for x in ("jakim", "tone", "ze", "manel")]
#instances = "ABCD"
#sequential = Experiment(methods, instances)
#parallel = ParallelExperiment(methods, instances)

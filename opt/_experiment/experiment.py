from utils.namespace import Namespace
from utils.logger import Logger
from utils.clock import Clock


class Experiment(object):
    """An abstract computational experiment. A set of candidate methods is run on a set of 
    instances and results are extracted and saved."""
    def __init__(self):
        self.log = Logger()
        self.log_block = None
        self.clock = None
        self.params = None
        
    def execute(self, replications=1, **params):
        self.setup(**params)
        self.run(replications)
        self.finalize()
        
    def setup(self, **params):
        self.log.info("Setting up experiment...")
        self.log_block = dict(instance=None, method=None, replication=None)
        self.clock = Clock()
        self.params = Namespace(params)
        self.params.experiment = self
        self.params.log = self.log
        self.on_setup()
        
    def run(self, replications=1):
        self.log.info("Running experiment...")
        self.clock.start()
        self.replications = replications
        for self.instance in self.iter_instances():
            for self.method in self.iter_methods():
                for self.replication in self.iter_replications():
                    self.save_results(self.method(**self.params))
                self.replication = None
            self.method = None
        self.instance = None
        self.clock.stop()
        self.log.info("Experiment completed in %.3f seconds.", self.clock.total)
        
    def finalize(self):
        self.log.info("Finalizing experiment...")
        self.on_finalize()
        
    # --------------------------------------------------------------------------
    # Methods that **must** be defined in subclasses
    # --------------------------------------------------------------------------
    def on_setup(self):
        raise NotImplementedError()
        
    def on_finalize(self):
        raise NotImplementedError()
        
    def iter_instances(self):
        raise NotImplementedError()
        
    def iter_methods(self):
        raise NotImplementedError()
        
    def iter_replications(self):
        return xrange(self.replications)
        
    def save_results(self, results):
        raise NotImplementedError()
        
    # --------------------------------------------------------------------------
    # Auxiliary methods (mainly useful for logging)
    # --------------------------------------------------------------------------
    @property
    def instance(self):
        return self.params.instance
        
    @instance.setter
    def instance(self, instance):
        self.params.instance = instance
        self.set_log_block("instance", instance)
        
    @property
    def method(self):
        return self.params.method
        
    @method.setter
    def method(self, method):
        self.params.method = method
        self.set_log_block("method", method)
        
    @property
    def replication(self):
        return self.params.replication
        
    @replication.setter
    def replication(self, replication):
        self.params.replication = replication
        message = None if replication is None else ("Replication %s" % replication)
        self.set_log_block("replication", message)
        
    @property
    def replications(self):
        return self.params.replications
        
    @replications.setter
    def replications(self, replications):
        self.params.replications = replications
        
    def set_log_block(self, key, value):
        if self.log_block[key] is not None:
            self.log_block[key].exit()
            self.log_block[key] = None
        if value is not None:
            self.log_block[key] = self.log.info.block(value)
            self.log_block[key].enter()
            
            
            
if __name__ == "__main__":
    class TestExperiment(Experiment):
        def on_setup(self):
            self.log.info("Setup complete!")
        
        def on_finalize(self):
            self.log.info("Experiment finished.")
        
        def iter_instances(self):
            return iter("ABCDEF")
        
        def iter_methods(self):
            for name in "xyzw":
                def method(**params):
                    pass
                method.__name__ = name
                yield method
                
        def iter_replications(self):
            return xrange(self.replications)
            
        def save_results(self, results):
            pass
            
            
    t = TestExperiment()
    t.execute()
    

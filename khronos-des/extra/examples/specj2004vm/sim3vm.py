"""
Modified version from the previous specj2004 model, to incorporate the sharing of physical cpus 
by the virtual machines.
"""
from sys import stdout

from khronos.des import Simulator, Process
from khronos.utils import Namespace, Reportable

from resources import PhysicalCPU, VirtualCPU, CPUBalancer, DiskFIFO as Disk, AutoStop
from transactions import DealerTransaction, Browse, Purchase, Manage, WorkOrder, LargeOrder

class SPECj2004Sim(Simulator):
    def reset(self):
        config = self.config
        for ttype in [Browse, Purchase, Manage, WorkOrder, LargeOrder]:
            ttype.service_time = config.service_time[ttype.__name__]
            ttype.response.clear()
            ttype.autoname_reset()
        DealerTransaction.mix = config.mix
        self.build()
        
    def build(self):
        self.members.clear()
        config = self.config
        tree = self.tree
        tree["stopper"] = AutoStop(ttypes=(Browse, Purchase, Manage, WorkOrder, LargeOrder))
        tree["mfg"] = Process()
        for x in xrange(3 * config.IR):
            tree["mfg"].add(WorkOrder())
        tree["dlr"] = Process()
        for x in xrange(10 * config.IR):
            tree["dlr"].add(DealerTransaction.next_type(self.rng)())
        tree["SUT"] = Process()
        tree["SUT.pCPU"] = CPUBalancer()
        for x in xrange(config.ncores):
            tree["SUT.pCPU"].add(PhysicalCPU(x))
        tree["SUT.LB"] = VirtualCPU(pCPU=tree["SUT.pCPU"])
        tree["SUT.AS"] = CPUBalancer()
        for x in xrange(2):
            tree["SUT.AS"].add(VirtualCPU(x, pCPU=tree["SUT.pCPU"]))
        tree["SUT.DB"] = Process()
        tree["SUT.DB.cpu"] = VirtualCPU(pCPU=tree["SUT.pCPU"])
        tree["SUT.DB.disk"] = Disk()
        tree["SUT.Dom0"] = VirtualCPU(pCPU=tree["SUT.pCPU"])
        
    def finalize(self):
        self.simulation.results.update(self.compute_results())
        self.print_results(self.simulation.results)
        
    def compute_results(self):
        results = Namespace(txcount=Namespace(),
                            response=Namespace(),
                            throughput=Namespace(), 
                            utilization=Namespace())
        for ttype in [Browse, Purchase, Manage, WorkOrder, LargeOrder]:
            results.txcount[ttype.__name__]    = ttype.response.count()
            results.response[ttype.__name__]   = ttype.response.mean()
            results.throughput[ttype.__name__] = ttype.response.count() / (self.time / 1000.0)
        utz = results.utilization
        utz.LB      = self.tree["SUT.LB"].pCPU_utz.wmean() * 100.0
        utz.AS      = sum([vCPU.pCPU_utz.wmean() for vCPU in self.tree["SUT.AS"]]) * 100.0
        utz.DB_cpu  = self.tree["SUT.DB.cpu"].pCPU_utz.wmean() * 100.0
        utz.DB_disk = self.tree["SUT.DB.disk"].utilization()
        utz.Dom0    = self.tree["SUT.Dom0"].pCPU_utz.wmean() * 100.0
        utz.pCPU    = self.tree["SUT.pCPU"].utilization()
        utz.Core0   = self.tree["SUT.pCPU.0"].utilization()
        utz.Core1   = self.tree["SUT.pCPU.1"].utilization()
        return results
        
    def print_results(self, results=None, out=stdout):
        if results is None:
            results = self.compute_results()
        utz = results.utilization
        ttypes = ("Browse", "Purchase", "Manage", "WorkOrder", "LargeOrder")
        items = [("Completed transactions", ""), 
                 [(ttype, results.txcount[ttype]) for ttype in ttypes], 
                 ("Throughput (transactions/sec)", ""), 
                 [(ttype, results.throughput[ttype]) for ttype in ttypes], 
                 ("Response time (ms)", ""), 
                 [(ttype, results.response[ttype]) for ttype in ttypes], 
                 ("Utilization (%)", ""), 
                 [("Load balancer",      utz.LB), 
                  ("Application server", utz.AS), 
                  ("DB cpu",             utz.DB_cpu), 
                  ("DB disk",            utz.DB_disk),
                  ("Dom0",               utz.Dom0),
                  ("Physical CPU",  "%f (total %f)" % (utz.pCPU, utz.Core0 + utz.Core1)),
                  [("Core0", utz.Core0),
                   ("Core1", utz.Core1)]]]
        out.write(Reportable.report(items))
        out.write("\n")
        out.flush()
        
from params import mix0, servtime_3vm, servtime_3vm_disk, servtime_3vm_double
sim = SPECj2004Sim("sim", config=Namespace(service_time=servtime_3vm_double, 
                                           mix=mix0, IR=2, ncores=2))
sim.stack.trace = False

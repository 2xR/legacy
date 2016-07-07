from khronos.statistics import Plotter
from khronos.utils import Namespace

from sim3vm import SPECj2004Sim
from params import mix0, servtime_3vm, servtime_3vm_disk, servtime_3vm_double

default_config = Namespace(service_time=servtime_3vm_double, ncores=2, mix=mix0)

def run(max_duration=3600000.0, config=default_config, 
        IRs=range(2, 15, 3), output_file="results.txt"):
    with open(output_file, "w") as out:
        pass # this is just to touch the file and delete previous contents
    sim = SPECj2004Sim("sim", config=config)
    sim.stack.trace = False
    for sim.config.IR in IRs:
        simulation = sim.single_run(max_duration, seed=0)
        with open(output_file, "a") as out:
            out.write("IR=%d, simulation ended at %f\n" % (sim.config.IR, sim.time))
            sim.print_results(simulation.results, out)
            
def plot(dlr_throughput, mfg_throughput):
    IRs    = sorted(dlr_throughput.iterkeys())
    dlr_ys = [dlr_throughput[IR] for IR in IRs]
    mfg_ys = [mfg_throughput[IR] for IR in IRs]
    sum_ys = [dlr_throughput[IR] + mfg_throughput[IR] for IR in IRs]
    
    plt = Plotter()
    axes = Plotter.add_axes()
    plt.simple_plot(xs=IRs, ys=dlr_ys, marker="o", color="blue", label="Dlr", axes=axes)
    plt.simple_plot(xs=IRs, ys=mfg_ys, marker="o", color="green", label="Mfg", axes=axes)
    plt.simple_plot(xs=IRs, ys=sum_ys, marker="o", color="red", label="Total", axes=axes)
    plt.update()
    return plt
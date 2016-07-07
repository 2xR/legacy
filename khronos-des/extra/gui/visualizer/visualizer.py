from Tkinter import *

from khronos.utils import Namespace
from khronos.anim2d import Arena, Object2D
from khronos.tkwidgets import TabbedWindow
from khronos.des.extra.gui.visualizer.clock import SimClock
from khronos.des.extra.gui.visualizer.controls import SimControls
from khronos.des.extra.gui.visualizer.trace import TraceViewer
from khronos.des.extra.gui.visualizer.debug import DebugViewer
from khronos.des.extra.gui.visualizer.status import StatusViewer
from khronos.des.extra.gui.visualizer.reports import ReportViewer

class Visualizer(LabelFrame):
    """The visualizer is a mini-application that allows running and visualizing the evolution of 
    a model during a simulation. There are two possibilities for this, text (through the status() 
    method), or simple animated 2D graphics (using the Arena widget). The visualizer also offers 
    a trace viewer to provide detailed information about simulation events (for debugging), 
    controls to start, pause, and finish simulations, result visualization, and report generation
    capability."""
    def __init__(self, master, title="Simulation Visualizer"):
        LabelFrame.__init__(self, master, text=title)
        self.sim = None
        self.build()
        self.layout()
        self.bindings()
        self.setup_listeners()
        
    def build(self):
        w = self.widgets = Namespace()
        w.clock = SimClock(self)
        w.controls = SimControls(self)
        w.tabs = TabbedWindow(self, tab_side=LEFT)
        w.arena = Arena(w.tabs.widgets.main, title="Animation", autoupdate=False)
        w.status = StatusViewer(w.tabs.widgets.main, title="Status")
        w.trace = TraceViewer(w.tabs.widgets.main, title="Trace")
        w.debug = DebugViewer(w.tabs.widgets.main, title="Debug")
        w.reports = ReportViewer(w.tabs.widgets.main, title="Reports")
        w.tabs.add(w.arena, "Animation")
        w.tabs.add(w.status, "Status")
        w.tabs.add(w.trace, "Trace")
        w.tabs.add(w.debug, "Debug")
        w.tabs.add(w.reports, "Reports")
        
    def layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        w = self.widgets
        w.tabs.grid(row=0, column=0, rowspan=2, sticky=N+S+E+W)
        w.clock.grid(row=0, column=1, sticky=N+S+E+W)
        w.controls.grid(row=1, column=1, sticky=N+S+E+W)
        
    def bindings(self):
        self.bind("<Map>", self.bind_keys)
        self.bind("<Unmap>", self.unbind_keys)
        
    def bind_keys(self, event):
        for key in ("A", "S", "R", "D", "T"):
            self.bind_all("<Control-Shift-KeyPress-%s>" % (key,), self.switch_tab)
            
    def unbind_keys(self, event):
        for key in ("A", "S", "R", "D", "T"):
            self.unbind_all("<Control-Shift-KeyPress-%s>" % (key,))
            
    def switch_tab(self, event):
        w = self.widgets
        key_map = {"A": w.arena, 
                   "S": w.status, 
                   "R": w.reports, 
                   "T": w.trace,
                   "D": w.debug}
        w.tabs.show_tab(w.tabs.get_id(key_map[event.keysym]))
        
    def setup_listeners(self):
        sigmanager = self.widgets.controls.sigmanager
        for wname in ("clock", "status", "trace"):
            self.widgets[wname].setup_listeners(sigmanager)
        sigmanager.add_listener("sim_start", self.sim_start)
        sigmanager.add_listener("sim_update", self.sim_update)
        
    def set_sim(self, sim):
        self.sim = sim
        self.sim.arena = self.widgets.arena
        self.widgets.arena.clear()
        self.widgets.controls.set_sim(sim)
        
    def del_sim(self):
        if self.sim is not None:
            self.sim.arena = None
            self.sim = None
        self.widgets.arena.clear()
        self.widgets.controls.del_sim()
        
    def sim_start(self):
        self.widgets.arena.clear()
        for comp, depth in self.sim.tree_iter():
            if isinstance(comp, Object2D):
                self.widgets.arena.add(comp)
                
    def sim_update(self):
        self.widgets.arena.update_idletasks()
        

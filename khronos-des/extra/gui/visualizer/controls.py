from Tkinter import *
from contextlib import contextmanager

from khronos.utils import Namespace
from khronos.des.extra.gui.common import SignalManager

class SimControls(LabelFrame):
    def __init__(self, master, title="Controls"):
        LabelFrame.__init__(self, master, text=title)
        self.sim = None
        self.sigmanager = SignalManager()
        self.enabled = False
        self.build()
        self.layout()
        self.bindings()
        
    def build(self):
        w = self.widgets = Namespace()
        w.start = Button(self, text="Start", state=DISABLED, command=self.start)
        w.step  = Button(self, text="Step",  state=DISABLED, command=self.step)
        w.leap  = Button(self, text="Leap",  state=DISABLED, command=self.leap)
        w.run   = Button(self, text="Run",   state=DISABLED, command=self.run)
        w.stop  = Button(self, text="Stop",  state=DISABLED, command=self.stop)
        w.scale = Scale(self, command=self.set_scale, from_=100.0, to=0.0, resolution=1.0, 
                        tickinterval=25.0, length=100, orient=VERTICAL, 
                        label="RT Scale", state=DISABLED)
                        
    def layout(self):
        w = self.widgets
        w.start.pack(side=TOP, fill=X)
        w.step.pack(side=TOP, fill=X)
        w.leap.pack(side=TOP, fill=X)
        w.run.pack(side=TOP, fill=X)
        w.stop.pack(side=TOP, fill=X)
        w.scale.pack(side=TOP)
        
    def bindings(self):
        self.bind("<Map>", self.bind_keys)
        self.bind("<Unmap>", self.unbind_keys)
        
    def bind_keys(self, event=None):
        if self.enabled:
            self.bind_all("<KeyPress-space>", self.toggle_run)
            self.bind_all("<KeyPress-s>", self.step)
            self.bind_all("<KeyPress-l>", self.leap)
            self.bind_all("<KeyPress-+>", self.inc_scale)
            self.bind_all("<KeyPress-->", self.dec_scale)
            self.bind_all("<Control-KeyPress-+>", self.super_inc_scale)
            self.bind_all("<Control-KeyPress-->", self.super_dec_scale)
            
    def unbind_keys(self, event=None):
        self.unbind_all("<KeyPress-space>")
        self.unbind_all("<KeyPress-+>")
        self.unbind_all("<KeyPress-->")
        self.unbind_all("<KeyPress-s>")
        self.unbind_all("<KeyPress-l>")
        self.unbind_all("<Control-KeyPress-+>")
        self.unbind_all("<Control-KeyPress-->")
        
    def set_sim(self, sim):
        self.sim = sim
        self.enable_all()
        self.widgets.scale.set(0.0 if sim.clock.scale is None else sim.clock.scale)
        self.sigmanager.signal("set_sim", sim)
        
    def del_sim(self):
        if self.sim is not None:
            self.pause()
        self.disable_all()
        self.sim = None
        self.sigmanager.signal("del_sim")
        
    def enable_all(self):
        for wname in ("start", "step", "leap", "run", "stop", "scale"):
            self.widgets[wname].configure(state=NORMAL)
        self.enabled = True
        self.bind_keys()
        
    def disable_all(self):
        for wname in ("start", "step", "leap", "run", "stop", "scale"):
            self.widgets[wname].configure(state=DISABLED)
        self.enabled = False
        self.unbind_keys()
        
    @contextmanager
    def disabled_all(self):
        self.disable_all()
        yield
        self.enable_all()
        
    def start(self):
        if self.sim.running:
            return
        with self.disabled_all():
            self.sim.start()
        self.sigmanager.signal("sim_start")
        
    def step(self, event=None):
        if not self.sim.running:
            self.start()
        with self.disabled_all():
            self.sim.step()
        self.sigmanager.signal("sim_update")
        
    def leap(self, event=None):
        if not self.sim.running:
            self.start()
        with self.disabled_all():
            self.sim.leap()
        self.sigmanager.signal("sim_update")
        
    def run(self):
        if not self.sim.running:
            self.start()
        self.disable_all()
        self.bind_all("<KeyPress-space>", self.toggle_run)
        self.widgets.run.configure(state=NORMAL, text="Pause", command=self.pause)
        self.__run()
        
    def __run(self):
        if self.widgets.run.cget("text") == "Pause":
            self.sim.leap()
            self.sigmanager.signal("sim_update")
            if len(self.sim.schedule.dates) == 0:
                self.widgets.run.configure(text="Run", command=self.run)
                self.stop()
            else:
                self.after(0, self.__run)
                
    def pause(self):
        self.widgets.run.configure(text="Run", command=self.run)
        self.enable_all()
        
    def stop(self):
        with self.disabled_all():
            self.sim.stop()
        self.sigmanager.signal("sim_stop")
        
    def toggle_run(self, event):
        if self.sim is not None:
            if self.widgets.run.cget("text") == "Run":
                self.run()
            else:
                self.pause()
                
    def set_scale(self, s):
        if self.sim is not None:
            s = float(s)
            if s <= 0.0:
                self.sim.clock.scale = None
            else:
                self.sim.clock.scale = s / 100.0
                
    def inc_scale(self, event):
        scale = self.widgets.scale
        scale.set(scale.get() + float(scale["resolution"]))
        
    def dec_scale(self, event):
        scale = self.widgets.scale
        scale.set(scale.get() - float(scale["resolution"]))
        
    def super_inc_scale(self, event):
        scale = self.widgets.scale
        scale.set(scale.get() + 10 * float(scale["resolution"]))
        
    def super_dec_scale(self, event):
        scale = self.widgets.scale
        scale.set(scale.get() - 10 * float(scale["resolution"]))
        

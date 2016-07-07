from Tkinter import *
from tkFont import Font

from khronos.utils import Namespace

class SimClock(LabelFrame):
    def __init__(self, master, title="Clock"):
        LabelFrame.__init__(self, master, text=title)
        self.sim = None
        self.font = Font(family="Courier New", size=10, weight="bold")
        self.build()
        self.layout()
        
    def build(self):
        w = self.widgets = Namespace()
        w.value = Label(self, text="N/A", font=self.font)
        
    def layout(self):
        self.columnconfigure(0, weight=1)
        self.widgets.value.grid(row=0, column=0, sticky=E)
        
    def setup_listeners(self, sigmanager):
        sigmanager.add_listener("set_sim", self.set_sim)
        sigmanager.add_listener("del_sim", self.del_sim)
        sigmanager.add_listener("sim_start", self.sim_update)
        sigmanager.add_listener("sim_update", self.sim_update)
        
    def set_sim(self, sim):
        self.sim = sim
        self.sim_update()
        
    def del_sim(self):
        self.sim = None
        self.widgets.value.configure(text="N/A")
        
    def sim_update(self):
        self.widgets.value.configure(text="%.03f" % (self.sim.time,))
        

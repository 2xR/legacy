from Tkinter import *
from tkFont import Font
from cStringIO import StringIO

from khronos.utils import Namespace

class StatusViewer(LabelFrame):
    def __init__(self, master, title="Status", width=80, height=10, fontsize=12):
        LabelFrame.__init__(self, master, text=title)
        self.sim = None
        self.build(width, height, fontsize)
        self.layout()
        
    def build(self, width, height, fontsize):
        w = self.widgets = Namespace()
        w.text = Text(self, width=width, height=height, state=DISABLED, wrap=NONE, 
                      undo=False, font=Font(family="Courier New", size=fontsize))
        w.xscroll = Scrollbar(self, orient=HORIZONTAL, command=w.text.xview)
        w.yscroll = Scrollbar(self, orient=VERTICAL,   command=w.text.yview)
        w.text.configure(xscrollcommand=w.xscroll.set, yscrollcommand=w.yscroll.set)
        
    def layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        w = self.widgets
        w.text.grid(row=0, column=0, stick=N+S+E+W)
        w.yscroll.grid(row=0, column=1, sticky=N+S)
        w.xscroll.grid(row=1, column=0, sticky=E+W)
        
    def clear(self):
        text = self.widgets.text
        text.configure(state=NORMAL)
        text.delete("0.0", END)
        text.configure(state=DISABLED)
        
    def setup_listeners(self, sigmanager):
        sigmanager.add_listener("set_sim", self.set_sim)
        sigmanager.add_listener("del_sim", self.del_sim)
        sigmanager.add_listener("sim_start", self.sim_update)
        sigmanager.add_listener("sim_stop", self.sim_update)
        sigmanager.add_listener("sim_update", self.sim_update)
        
    def set_sim(self, sim):
        self.sim = sim
        
    def del_sim(self):
        self.clear()
        self.sim = None
        
    def sim_update(self):
        string = StringIO()
        self.sim.tree_status(out=string)
        text = self.widgets.text
        text.configure(state=NORMAL)
        text.delete("0.0", END)
        text.insert(END, string.getvalue())
        text.configure(state=DISABLED)
        

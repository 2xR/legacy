from Tkinter import *
from tkFont import Font
from sys import stdout

from khronos.utils import Namespace

class TraceViewer(LabelFrame):
    def __init__(self, master, title="Trace", width=80, height=10, fontsize=12):
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
        w.controls = Frame(self)
        w.trace_var = IntVar(0)
        w.trace_clear = Button(w.controls, text="Clear", command=self.clear, state=DISABLED)
        w.trace = Checkbutton(w.controls, text="Trace", command=self.set_trace, 
                              variable=w.trace_var, state=DISABLED)
        
    def layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        w = self.widgets
        w.text.grid(row=0, column=0, sticky=N+S+E+W)
        w.yscroll.grid(row=0, column=1, sticky=N+S)
        w.xscroll.grid(row=1, column=0, sticky=E+W)
        w.controls.grid(row=0, column=2, sticky=N+E+W)
        w.trace.grid(row=0, column=0, sticky=N+E+W)
        w.trace_clear.grid(row=1, column=0, sticky=N+E+W)
        
    def clear(self):
        text = self.widgets.text
        text.configure(state=NORMAL)
        text.delete("0.0", END)
        text.configure(state=DISABLED)
        
    def write(self, msg):
        text = self.widgets.text
        text.configure(state=NORMAL)
        text.insert(END, msg)
        text.yview_moveto(1.0)
        text.configure(state=DISABLED)
        
    def setup_listeners(self, sigmanager):
        sigmanager.add_listener("set_sim", self.set_sim)
        sigmanager.add_listener("del_sim", self.del_sim)
        
    def set_sim(self, sim):
        self.sim = sim
        self.sim.stack.trace_out = self
        self.widgets.trace_var.set(sim.stack.trace)
        for wname in ("trace", "trace_clear"):
            self.widgets[wname].configure(state=NORMAL)
            
    def del_sim(self):
        if self.sim is not None:
            self.sim.stack.trace_out = stdout
        self.clear()
        for wname in ("trace", "trace_clear"):
            self.widgets[wname].configure(state=DISABLED)
            
    def set_trace(self):
        self.sim.stack.trace = bool(self.widgets.trace_var.get())
        

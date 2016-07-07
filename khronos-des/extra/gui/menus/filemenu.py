from tkFileDialog import askopenfilename
from tkMessageBox import showwarning
from os import path
import sys

from khronos.tkwidgets import FullMenu

class FileMenu(FullMenu):
    def __init__(self, master, name="File"):
        FullMenu.__init__(self, master, name)
        self.visualizer = None
        self.build()
        self.bindings()
        
    def build(self):
        self.menu.add_command(label="Open", command=self.open)
        self.menu.add_command(label="Save", command=self.save)
        self.menu.add_command(label="Save as...", command=self.save_as)
        self.menu.add_command(label="Close", command=self.close)
        
    def bindings(self):
        self.bind_all("<Control-KeyPress-o>", self.open)
        self.bind_all("<Control-KeyPress-w>", self.close)
        
    def link(self, visualizer):
        self.visualizer = visualizer
        
    def open(self, event=None, filepath=None):
        if filepath is None:
            filepath = askopenfilename(initialdir=".", filetypes=[("Python", ".py")])
        if filepath:
            sys.path.insert(0, path.dirname(filepath))
            module = __import__(path.basename(filepath)[:-3])
            sys.path.pop(0)
            self.visualizer.del_sim()
            self.visualizer.set_sim(module.sim)
            
    def save(self, event=None):
        showwarning("Unavailable", "Feature not implemented yet")
        
    def save_as(self, event=None):
        showwarning("Unavailable", "Feature not implemented yet")
        
    def close(self, event=None):
        self.visualizer.del_sim()
        

from Tkinter import *

from khronos.utils import Namespace
from khronos.tkwidgets import TabbedWindow
from khronos.des.extra.gui.menus import MenuBar
from khronos.des.extra.gui.visualizer import Visualizer
from khronos.des.extra.gui.modeler import Modeler
from khronos.des.extra.gui.developer import Developer

class KhronosSDE(Frame):
    """SDE stands for simulation development environment. This class is nothing more than a frame 
    merging three mini-applications related to Khronos. The applications are: the visualizer, to 
    run and visualize animated simulations; the modeler, to assemble models from simulation 
    components and connections imported from component libraries; the developer, to create new 
    simulation components with user-specified behavior."""
    #optionfile = "./options.txt"
    def __init__(self, master):
        #self.option_readfile(self.optionfile)
        Frame.__init__(self, master)
        self.build()
        self.layout()
        self.link()
        self.bindings()
        
    def build(self):
        w = self.widgets = Namespace()
        w.menubar = MenuBar(self)
        w.tabs = TabbedWindow(self, tab_side=BOTTOM)
        w.visualizer = Visualizer(w.tabs.widgets.main)
        w.modeler = Modeler(w.tabs.widgets.main)
        w.developer = Developer(w.tabs.widgets.main)
        w.tabs.add(w.visualizer, "Visualizer")
        w.tabs.add(w.modeler, "Modeler")
        w.tabs.add(w.developer, "Developer")
        
    def layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        
        w = self.widgets
        w.menubar.grid(row=0, column=0, sticky=N+S+E+W)
        w.tabs.grid(row=1, column=0, sticky=N+S+E+W)
        
    def link(self):
        w = self.widgets
        w.menubar.widgets.file.link(w.visualizer)
        w.menubar.widgets.run.link(w.visualizer.widgets.controls)
        
    def bindings(self):
        self.bind_all("<Control-Alt-KeyPress-v>", self.switch_app)
        self.bind_all("<Control-Alt-KeyPress-m>", self.switch_app)
        self.bind_all("<Control-Alt-KeyPress-d>", self.switch_app)
        
    def switch_app(self, event):
        w = self.widgets
        key_map = {"v": w.visualizer, 
                   "m": w.modeler, 
                   "d": w.developer}
        w.tabs.show_tab(w.tabs.get_id(key_map[event.keysym]))
        
def SimApp():
    """Starts an application containing a KhronosSDE frame."""
    app = Tk()
    app.title("Khronos Simulation Development Environment")
    app.iconbitmap("./khronos_green.ico")
    app.minsize(600, 400)
    app.rowconfigure(0, weight=1)
    app.columnconfigure(0, weight=1)
    
    sde = KhronosSDE(app)
    sde.grid(row=0, column=0, sticky=N+S+E+W)
    return sde
    
if __name__ == "__main__":
    SimApp().mainloop()
    
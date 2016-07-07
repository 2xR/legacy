from tkMessageBox import showwarning

from khronos.tkwidgets import FullMenu

def unavailable(self):
    showwarning("Unavailable", "Feature not implemented yet")
    
class RunMenu(FullMenu):
    def __init__(self, master, name="Run"):
        FullMenu.__init__(self, master, name)
        self.controls = None
        self.build()
        
    def build(self):
        self.menu.add_command(label="Start", command=self.start)
        self.menu.add_command(label="Step", command=self.step)
        self.menu.add_command(label="Leap", command=self.leap)
        self.menu.add_command(label="Run/Pause", command=self.toggle_run)
        self.menu.add_command(label="Stop", command=self.stop)
        
    def link(self, controls):
        self.controls = controls
        
    start = unavailable
    step = unavailable
    leap = unavailable
    toggle_run = unavailable
    stop = unavailable
    

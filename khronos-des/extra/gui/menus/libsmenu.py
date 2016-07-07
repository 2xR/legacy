from tkMessageBox import showwarning

from khronos.tkwidgets import FullMenu

class LibsMenu(FullMenu):
    def __init__(self, master, name="Libraries"):
        FullMenu.__init__(self, master, name)
        self.menu.add_command(label="Load", command=self.load)
        self.menu.add_command(label="Unload", command=self.unload)
        
    def load(self):
        showwarning("Unavailable", "Feature not implemented yet")
        
    def unload(self):
        showwarning("Unavailable", "Feature not implemented yet")
        

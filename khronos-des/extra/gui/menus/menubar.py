from Tkinter import *

from khronos.utils import Namespace
from khronos.des.extra.gui.menus.filemenu import FileMenu
from khronos.des.extra.gui.menus.runmenu import RunMenu
from khronos.des.extra.gui.menus.libsmenu import LibsMenu
from khronos.des.extra.gui.menus.helpmenu import HelpMenu

class MenuBar(Frame):
    def __init__(self, master):
        Frame.__init__(self, master)
        self.build()
        self.layout()
        
    def build(self):
        w = self.widgets = Namespace()
        w.file = FileMenu(self)
        w.run  = RunMenu(self)
        w.libs = LibsMenu(self)
        w.help = HelpMenu(self)
        
    def layout(self):
        w = self.widgets
        for name in ("file", "run", "libs", "help"):
            w[name].pack(side=LEFT, fill=Y)
            

from tkMessageBox import showinfo

from khronos.tkwidgets import FullMenu

class HelpMenu(FullMenu):
    def __init__(self, master, name="Help"):
        FullMenu.__init__(self, master, name)
        self.menu.add_command(label="Keyboard shortcuts", command=self.shortcuts)
        self.menu.add_command(label="About Khronos", command=self.about)
        
    def shortcuts(self):
        global keyboard_shortcuts
        showinfo("Keyboard shortcuts", keyboard_shortcuts)
        
    def about(self):
        """Display a simple 'about' message about khronos and the GUI."""
        global about_message
        showinfo("About Khronos", about_message)
        
keyboard_shortcuts = """Global shortcuts
    [Ctrl + Alt + v] switch to Visualizer
    [Ctrl + Alt + m] switch to Modeler
    [Ctrl + Alt + d] switch to Developer
    
    [Ctrl + o] open file
    [Ctrl + w] close file
    
Visualizer shortcuts
    [Ctrl + Shift + a] switch to Animation tab
    [Ctrl + Shift + s] switch to Status tab
    [Ctrl + Shift + t] switch to Trace tab
    [Ctrl + Shift + r] switch to Reports tab
    
    [s] run a simulation step
    [l] run a simulation leap
    [space] toggle simulation run/pause"""
    
about_message = """Khronos is a discrete-event simulation library for Python 2.6+

Beginner tutorials and reference manuals can be found at khronos-des.sourceforge.net. 
Offline documentation and examples can be found in the installation directory.

Author: Rui Jorge Rei
Email: rui.jorge.rei@googlemail.com"""

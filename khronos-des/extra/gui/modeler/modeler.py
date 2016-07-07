from khronos.tkwidgets import DummyWidget

def Modeler(master):
    return DummyWidget(master, 800, 600, "Model Designer")
    
##from Tkinter import *
##from utils import Namespace
##
##class Modeler(Frame):
##    """This frame"""
##    def __init__(self, master):
##        Frame.__init__(self, master)
##        self.libs = None     # Component libraries currently loaded
##        self.components = {} # Components currently available for modeling
##        
##        self.build()
##        self.layout()
##        
##    def build(self):
##        w = self.widgets = Namespace()
##        w.buttons = Frame(self)
##        w.load = Button(w.buttons, )
        

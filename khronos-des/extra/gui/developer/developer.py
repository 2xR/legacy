from khronos.tkwidgets import DummyWidget

def Developer(master):
    return DummyWidget(master, 800, 600, "Component Developer")
    
#from Tkinter import *
#from khronos.utils import Namespace
#from sys import stdout
#
#class ActualDeveloper(LabelFrame):
#    """This is a mini-application which provides a graphical interface to writing simulation 
#    components out of primitives and smaller components."""
#    def __init__(self, master, title="Component Developer"):
#        LabelFrame.__init__(self, master, text=title)
#        self.build()
#        self.layout()
#        
#    def build(self):
#        w = self.widgets = Namespace()
#        
#        
#class Component(object):
#    """Represents an atomic component."""
#    name = "Component"
#    type = "Atomic"
#    super = []
#    in_ports = {}
#    out_ports = {}
#    initialize = None
#    methods = []
#    
#    def write(self, out=stdout):
#        superclasses = ", ".join(["Process.%s" % (self.type,)] + self.super)
#        out.write("class %s(%s):\n" % (self.name, superclasses))
#        self.initialize.write(out)
#        for method in self.methods:
#            method.write(out)
#            
#class Indicator(object):
#    pass
#    
#class Port(object):
#    """Represents an input or output port."""
#    
#class Connection(object):
#    """Represents a connection between two ports."""
#    
#class Chain(object):
#    pass
#    
#class Block(list):
#    pass
#    
#class Method(object):
#    def __init__(self, arguments=NO_ARGS, body=EMPTY_BLOCK):
#        pass
#        

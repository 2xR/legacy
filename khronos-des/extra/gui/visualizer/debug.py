from khronos.tkwidgets import DummyWidget

def DebugViewer(master, title):
    return DummyWidget(master, 800, 600, title)
    
"""Here the user should be able to inspect the internal structures of the simulator, like the 
event schedule."""
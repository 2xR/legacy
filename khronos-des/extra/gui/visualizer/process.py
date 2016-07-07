from khronos.des import Process
from khronos.anim2d import Object2D

class AnimatedProcess(Process, Object2D):
    def __init__(self, name=None, parent=None, members=(), 
                 pos=(0, 0), heading=0.0, shape=None, **kwargs):
        Process.Atomic.__init__(self, name, parent, members, **kwargs)
        Object2D.__init__(self, pos, heading, shape)
        
from khronos.des.primitives.operators.unary_op import UnaryOp
from khronos.utils import INF

class Repeat(UnaryOp):
    def __init__(self, operand, times=INF):
        UnaryOp.__init__(self, operand)
        self.times = times
        self.counter = 0
        
    def __info__(self):
        return "<%d/%s> %s" % (self.counter, self.times, self.operand)
        
    def reset(self):
        UnaryOp.reset(self)
        self.counter = 0
        
    def succeed(self):
        self.operand.succeed()
        
    def fail(self):
        self.operand.fail()
        
    def child_succeeded(self, child):
        if child is not self.operand:
            raise ValueError("invalid child action provided")
        self.counter += 1
        if self.counter < self.times:
            self.operand.start()
        else:
            UnaryOp.succeed(self)
            
    def child_failed(self, child):
        if child is not self.operand:
            raise ValueError("invalid child action provided")
        UnaryOp.fail(self)
        

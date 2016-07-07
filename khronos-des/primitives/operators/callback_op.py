from khronos.des.primitives.operators.unary_op import UnaryOp

def dummy_fnc():
    pass
    
class Callback(UnaryOp):
    def __init__(self, operand, on_succeed=dummy_fnc, on_fail=dummy_fnc):
        UnaryOp.__init__(self, operand)
        self.on_succeed = on_succeed
        self.on_fail = on_fail
        
    def __info__(self):
        return "%s if %s else %s" % (self.on_succeed.__name__, self.operand, self.on_fail.__name__)
        
    def succeed(self):
        self.operand.succeed()
        
    def fail(self):
        self.operand.fail()
        
    def child_succeeded(self, child):
        if child is not self.operand:
            raise ValueError("invalid child action provided")
        with self.in_stack("C"):
            self.on_succeed()
            UnaryOp.succeed(self)
            
    def child_failed(self, child):
        if child is not self.operand:
            raise ValueError("invalid child action provided")
        with self.in_stack("C"):
            self.on_fail()
            UnaryOp.fail(self)
            

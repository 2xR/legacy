from khronos.des.primitives.operators.unary_op import UnaryOp

class Not(UnaryOp):
    def child_succeeded(self, child):
        if child is not self.operand:
            raise ValueError("invalid child action provided")
        self.fail()
        
    def child_failed(self, child):
        if child is not self.operand:
            raise ActionError("invalid child action provided")
        self.succeed()
        
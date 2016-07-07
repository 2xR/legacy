from khronos.des.primitives.operators.multary_op import MultaryOp

class And(MultaryOp):
    def child_succeeded(self, child):
        self.operands_remaining.remove(child)
        self.operands_succeeded.append(child)
        if len(self.operands_remaining) == 0:
            self.succeed()
            
    def child_failed(self, child):
        self.operands_remaining.remove(child)
        self.operands_failed.append(child)
        self.fail()
        
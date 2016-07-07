from khronos.des.primitives.operators.multary_op import MultaryOp

class Or(MultaryOp):
    def child_succeeded(self, child):
        self.operands_remaining.remove(child)
        self.operands_succeeded.append(child)
        self.succeed()
        
    def child_failed(self, child):
        self.operands_remaining.remove(child)
        self.operands_failed.append(child)
        if len(self.operands_remaining) == 0:
            self.fail()
            
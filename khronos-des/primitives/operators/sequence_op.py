from khronos.des.primitives.operators.multary_op import MultaryOp

class Sequence(MultaryOp):
    def deploy(self):
        self.operands_remaining[0].start()
        
    def retract(self):
        if len(self.operands_remaining) > 0:
            self.operands_remaining[0].cancel()
            
    def succeed(self):
        self.operands_remaining[0].succeed()
        
    def fail(self):
        self.operands_remaining[0].fail()
        
    def child_succeeded(self, child):
        if len(self.operands_remaining) == 0 or child is not self.operands_remaining[0]:
            raise ValueError("invalid child action provided")
        self.operands_remaining.popleft()
        self.operands_succeeded.append(child)
        if len(self.operands_remaining) == 0:
            MultaryOp.succeed(self)
        else:
            self.operands_remaining[0].start()
            
    def child_failed(self, child):
        if len(self.operands_remaining) == 0 or child is not self.operands_remaining[0]:
            raise ValueError("invalid child action provided")
        self.operands_remaining.popleft()
        self.operands_failed.append(child)
        MultaryOp.fail(self)
        
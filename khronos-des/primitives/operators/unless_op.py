from khronos.des.primitives.operators.binary_op import BinaryOp

class Unless(BinaryOp):
    """Reneging is a complex but important behavior in queueing systems. It represents doing one 
    action, but canceling it if some condition is true. The primitive 'Unless(A, B)' represents 
    the same logic in different terms: "unless A succeeds, do B".
        For example, a client at a bank requests a teller, but will renege that request if the 
    waiting time surpasses a given maximum. In khronos this could be something like:
        class Client(Process):
            @Chain
            def initialize(self):
                ...
                yield Unless(Delay(patience), teller.acquire())
                ...
    """
    def succeed(self):
        self.right_operand.succeed()
        
    def fail(self):
        self.right_operand.fail()
        
    def child_succeeded(self, child):
        if child is self.right_operand:
            BinaryOp.succeed(self)
        elif child is self.left_operand:
            BinaryOp.fail(self)
        else:
            raise ValueError("invalid child action provided")
            
    def child_failed(self, child):
        if child is self.right_operand:
            BinaryOp.fail(self)
        elif child is not self.left_operand:
            raise ValueError("invalid child action provided")
            
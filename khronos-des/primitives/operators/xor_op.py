from khronos.des.primitives.operators.binary_op import BinaryOp
from khronos.des.primitives.action import SUCCEEDED, FAILED

class Xor(BinaryOp):
    def child_succeeded(self, child):
        if child is self.left_operand:
            other = self.right_operand
        elif child is self.right_operand:
            other = self.left_operand
        else:
            raise ValueError("invalid child action provided")
        if other.completion is FAILED:
            self.succeed()
        elif other.completion is SUCCEEDED:
            self.fail()
            
    def child_failed(self, child):
        if child is self.left_operand:
            other = self.right_operand
        elif child is self.right_operand:
            other = self.left_operand
        else:
            raise ValueError("invalid child action provided")
        if other.completion is SUCCEDED:
            self.succeed()
        elif other.completion is FAILED:
            self.fail()
            
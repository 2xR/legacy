from khronos.des.primitives.action import Action
from khronos.utils import Deque

class MultaryOp(Action):
    def __init__(self, *operands):
        Action.__init__(self)
        self.operands = Deque()
        self.operands_remaining = Deque()
        self.operands_succeeded = Deque()
        self.operands_failed = Deque()
        for operand in operands:
            self.add_operand(operand)
            
    def add_operand(self, operand):
        if not isinstance(operand, Action):
            operand = Action.convert(operand)
        operand.link(self)
        self.operands.append(operand)
        
    def __info__(self):
        return ", ".join(str(operand) for operand in self.operands)
        
    def bind(self, owner):
        Action.bind(self, owner)
        for operand in self.operands:
            operand.bind(owner)
            
    def reset(self):
        self.operands_remaining = Deque(self.operands)
        self.operands_succeeded.clear()
        self.operands_failed.clear()
        
    def deploy(self):
        for operand in list(self.operands_remaining):
            operand.start()
            if self.completion is not None:
                self.retract()
                break
                
    def retract(self):
        for operand in self.operands_remaining:
            operand.cancel()
            

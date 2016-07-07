from khronos.des.primitives.action import Action

class UnaryOp(Action):
    def __init__(self, operand):
        Action.__init__(self)
        self.operand = operand if isinstance(operand, Action) else Action.convert(operand)
        self.operand.link(self)
        
    def __info__(self):
        return self.operand
        
    def bind(self, owner):
        Action.bind(self, owner)
        self.operand.bind(owner)
        
    def deploy(self):
        self.operand.start()
        
    def retract(self):
        self.operand.cancel()
        

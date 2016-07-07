from khronos.des.primitives.action import Action

class BinaryOp(Action):
    def __init__(self, left_op, right_op):
        Action.__init__(self)
        self.left_operand = left_op if isinstance(left_op, Action) else Action.convert(left_op)
        self.right_operand = right_op if isinstance(right_op, Action) else Action.convert(right_op)
        self.left_operand.link(self)
        self.right_operand.link(self)
        
    def __info__(self):
        return "%s, %s" % (self.left_operand, self.right_operand)
        
    def bind(self, owner):
        Action.bind(self, owner)
        self.left_operand.bind(owner)
        self.right_operand.bind(owner)
        
    def deploy(self):
        self.left_operand.start()
        if self.completion is None:
            self.right_operand.start()
            if self.completion is not None:
                self.retract()
                
    def retract(self):
        self.left_operand.cancel()
        self.right_operand.cancel()
        

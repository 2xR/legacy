from types import GeneratorType
from khronos.des.primitives.action import Action
from khronos.des.primitives.channel import Channel
from khronos.des.primitives.delay import Delay
from khronos.des.primitives.observer import Observer
from khronos.des.primitives.request import Request
from khronos.des.primitives.operators import (Callback, Chain, Unless, Repeat, 
                                              Sequence, And, Or, Xor, Not)

__all__ = ["Action", "Channel", "Delay", "Observer", "Request", "Callback", 
           "Chain", "Unless", "Repeat", "Sequence", "And", "Or", "Xor", "Not"]

# ---------------------------------------------------------
# Action operators setup
def and_op(x, y):
    if isinstance(x, And):
        x.add_operand(y)
        return x
    if isinstance(y, And):
        y.add_operand(x)
        return y
    return And(x, y)
    
def or_op(x, y):
    if isinstance(x, Or):
        x.add_operand(y)
        return x
    if isinstance(y, Or):
        y.add_operand(x)
        return y
    return Or(x, y)
    
def xor_op(x, y):
    return Xor(x, y)
    
def not_op(x):
    return Not(x)
    
def sequence_op(x, y):
    if isinstance(x, Sequence):
        x.add_operand(y)
        return x
    return Sequence(x, y)
    
def rsequence_op(x, y):
    return Sequence(y, x)
    
def repeat_op(x, n):
    return Repeat(x, n)
    
def observe_op(x):
    return Observer(x)
    
def convert_to_action(x):
    if isinstance(x, Action):
        return x
    if isinstance(x, GeneratorType):
        return Chain.from_generator(x)
    return Delay(x)
    
Action.__and__     = and_op
Action.__rand__    = and_op
Action.__or__      = or_op
Action.__ror__     = or_op
Action.__xor__     = xor_op
Action.__rxor__    = xor_op
Action.__invert__  = not_op
Action.__rshift__  = sequence_op
Action.__rrshift__ = rsequence_op
Action.__mul__     = repeat_op
Action.__rmul__    = repeat_op
Action.observe     = observe_op
Action.convert     = staticmethod(convert_to_action)

from gurobipy import quicksum
from utils.misc import check_type


class Unary(object):
    def __init__(self, expr):
        self.expr = expr


class Multary(object):
    def __init__(self, *exprs):
        self.children = list(exprs)


class Binary(object):
    def __init__(self, left, right):
        self.left = left
        self.right = right


class Not(Unary):
    pass


class And(Multary):
    pass

class Or(Multary):
    pass


class Implies(Binary):
    pass


class Equiv(Binary):
    pass



def to_cnf(expr):
    if isinstance(expr, And):
        return And(map(to_cnf, expr.children))
    if isinstance(expr, Or):
        exprs = list(expr.children)
        for i in xrange(len(exprs)):
            expr = exprs[i]
            if isinstance(expr, And):
                exprs = exprs[:i] + exprs[i+1:]
                return And(Or(expr.children[j], *exprs) for j in xrange(expr.children))

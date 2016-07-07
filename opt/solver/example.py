from opt.solver import Solver, Limit
from opt.infeasible import Infeasible


def identity_fnc(x):
    return x


class Foo(Solver):
    def __init__(self):
        Solver.__init__(self)
        self.sense = min
        self.objective = identity_fnc

    def _iterate(self):
        if self.rng.random() < 0.25:
            sol = Infeasible(self.rng.random())
        else:
            sol = self.rng.random()
        self.solutions.check(sol)


foo = Foo()
foo.init("anything other than None")
foo.run(Limit.Iters(10))

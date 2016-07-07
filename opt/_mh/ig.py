from khronos.opt.base import PathBasedSolver
from khronos.utils import INF

class IteratedGreedy(PathBasedSolver):
    """A generic implementation of an iterated greedy algorithm. Problem specific algorithms can 
    be implemented by sub-classing this class and defining the following methods:        
        initial_solution()            # create the starting point of the search
        destruction(solution)         # destroy part of a solution to obtain a partial solution
        construction(partial_sol)     # complete a partial solution obtained after destruction()
        acceptance(solution, prev_UB) # decide whether to move into the given solution or not 
    """
    def __init__(self):
        PathBasedSolver.__init__(self)
        self.current_solution = None
        self.cpu_limit = None
        self.init_params = None
        
    def init(self, instance=None, cpu=INF, initial_solution=None, **init_params):
        PathBasedSolver.init(self. instance)
        self.current_solution = initial_solution
        self.cpu_limit = cpu
        self.init_params = init_params
        
    def setup(self):
        with self.cpu.tracking():
            if self.current_solution is None:
                self.current_solution = self.initial_solution()
            self.add_solution(self.current_solution)
            self.path_tseries.collect(self.upper_bound, self.cpu.total)
            
    def path(self, cpu=None):
        if cpu is not None:
            self.cpu_limit = self.cpu.total + cpu
        self.bootstrap()
        while self.cpu.total < self.cpu_limit:
            with self.cpu.tracking():
                previous_UB = self.upper_bound
                partial_solution = self.destruction(self.current_solution)
                new_solution = self.construction(partial_solution)
                self.check_solution(new_solution)
                if self.acceptance(new_solution, previous_UB):
                    self.current_solution = new_solution
            yield self.current_solution
            
    def initial_solution(self):
        raise NotImplementedError()
        
    def destruction(self, solution):
        raise NotImplementedError()
        
    def construction(self, partial_solution):
        raise NotImplementedError()
        
    def acceptance(self, solution, previous_UB):
        return self.objective(solution) < previous_UB
        
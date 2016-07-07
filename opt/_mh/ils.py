from khronos.opt.base import PathBasedSolver
from khronos.utils import INF

class IteratedLocalSearch(PathBasedSolver):
    """A generic algorithm for iterated local search. Problem specific iterated local search 
    algorithms can be implemented by sub-classing this class and defining the following methods:
        initial_solution()            # create the starting point of the search
        perturbation(solution)        # perturb a given solution to create a new one 
        local_search(solution)        # perform a local search on the given solution
        acceptance(solution, prev_UB) # decide whether to move into the given solution or not
    """
    def __init__(self):
        PathBasedSolver.__init__(self)
        self.current_solution = None
        self.cpu_limit = None
        self.init_params = None
        
    def init(self, instance=None, cpu=INF, initial_solution=None, **init_params):
        PathBasedSolver.init(self, instance)
        self.current_solution = initial_solution
        self.cpu_limit = cpu
        self.init_params = init_params
        
    def setup(self):
        with self.cpu.tracking():
            if self.current_solution is None:
                self.current_solution = self.initial_solution()
            self.add_solution(self.current_solution)
            self.current_solution = self.local_search(self.current_solution)
            self.check_solution(self.current_solution)
            self.path_tseries.collect(self.upper_bound, self.cpu.total)
            
    def path(self, cpu=None):
        if cpu is not None:
            self.cpu_limit = self.cpu.total + cpu
        self.bootstrap()
        while self.cpu.total < self.cpu_limit:
            with self.cpu.tracking():
                previous_UB = self.upper_bound
                initial_solution = self.perturbation(self.current_solution)
                self.check_solution(initial_solution)
                local_optimum = self.local_search(initial_solution)
                self.check_solution(local_optimum)
                if self.acceptance(local_optimum, previous_UB):
                    self.current_solution = local_optimum
            yield self.current_solution
            
    def initial_solution(self):
        raise NotImplementedError()
        
    def perturbation(self, solution):
        raise NotImplementedError()
        
    def local_search(self, solution):
        raise NotImplementedError()
        
    def acceptance(self, solution, previous_UB):
        """By default, a solution is accepted only if its objective function value is smaller 
        than the previous upper bound."""
        return self.objective(solution) < previous_UB
        
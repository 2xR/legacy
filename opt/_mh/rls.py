from khronos.opt.base import PathBasedSolver
from khronos.utils import INF

class RepeatedLocalSearch(PathBasedSolver):
    """A generic algorithm for repeated local search. This can be used, e.g., for repeated local 
    search, GRASP, and other algorithms with similar structure. Problem specific repeated local 
    search algorithms can be implemented by sub-classing this class and defining the following 
    methods:
        initial_solution()     # create the starting point of the search
        generate_solution()    # create a solution for steps after the first step
        local_search(solution) # perform a local search on the given solution
    """
    def __init__(self):
        PathBasedSolver.__init__(self)
        self.starting_solution = None
        self.cpu_limit = None
        self.init_params = None
        
    def init(self, instance=None, cpu=INF, initial_solution=None, **init_params):
        PathBasedSolver.init(self, instance)
        self.starting_solution = initial_solution
        self.cpu_limit = cpu
        self.init_params = init_params
        
    def setup(self):
        with self.cpu.tracking():
            if self.starting_solution is None:
                self.starting_solution = self.initial_solution()
            self.add_solution(self.starting_solution)
            local_optimum = self.local_search(self.starting_solution)
            self.check_solution(local_optimum)
            self.path_tseries.collect(self.upper_bound, self.cpu.total)
            
    def path(self, cpu=None):
        if cpu is not None:
            self.cpu_limit = self.cpu.total + cpu
        self.bootstrap()
        while self.cpu.total < self.cpu_limit:
            with self.cpu.tracking():
                initial_solution = self.generate_solution()
                self.check_solution(initial_solution)
                local_optimum = self.local_search(initial_solution)
                self.check_solution(local_optimum)
            yield local_optimum
            
    def initial_solution(self):
        return self.generate_solution()
        
    def generate_solution(self):
        raise NotImplementedError()
        
    def local_search(self, solution):
        raise NotImplementedError()
        
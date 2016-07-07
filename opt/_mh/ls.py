from opt.solver import Solver
from utils import INF

class Uninitialized(Solver.Uninitialized):
    @staticmethod
    def enter(solver):
        pass
        
        
class Initialized(Solver.Initialized):
    @staticmethod
    def enter(solver, instance=None, initial_solution=None):
        Solver.Initialized.enter(solver, instance)
        solver.initial_solution = initial_solution
        

class Bootstrapped(Solver.Bootstrapped):
    @staticmethod
    def enter(solver):
        self.asd

class LocalSearch(Solver):
    """A generic implementation of local search. Problem specific local search algorithms can be 
    implemented by sub-classing this class and defining the following methods:        
        initial_solution()      # create the starting point of the local search
        neighborhood(solution)  # return the neighbors (iterable) of the given solution
    """
    check_neighborhood_print_interval = 100
    default_steepest_descent = True
    
    def __init__(self, log=None, steepest_descent=None):
        Solver.__init__(self, log)
        self.current_solution = None
        self.current_neighbors = None
        self.neighbors_checked = None
        self.best_neighbor = None
        self.steepest_descent = (steepest_descent if steepest_descent is not None 
                                 else self.default_steepest_descent)
        self.cpu_limit = None
        self.init_params = None
        
    def init(self, instance=None, cpu=INF, steepest_descent=None, 
             initial_solution=None, **init_params):
        PathBasedSolver.init(self, instance)
        if steepest_descent is not None:
            self.steepest_descent = steepest_descent
        self.cpu_limit = cpu
        self.init_params = init_params
        self.current_solution = initial_solution
        
    def setup(self):
        with self.cpu.tracking():
            if self.current_solution is None:
                self.current_solution = self.initial_solution()
            self.add_solution(self.current_solution)
            self.path_tseries.collect(self.upper_bound, self.cpu.total)
            self.best_neighbor = self.current_solution
            self._move_to_best_neighbor()
            
    def path(self, cpu=None):
        if cpu is not None:
            self.cpu_limit = self.cpu.total + cpu
        self.bootstrap()
        while self.cpu.total < self.cpu_limit:
            with self.cpu.tracking():
                if not self._check_neighborhood() or not self._move_to_best_neighbor():
                    return
            yield self.current_solution
            
    def _check_neighborhood(self):
        """Check the current neighborhood and record best neighbor. Returns a boolean indicating 
        whether the neighborhood check was completed or not.""" 
        completed = True
        self.log("Checking neighborhood... ", newline=False)
        for neighbor in self.current_neighbors:
            self.neighbors_checked += 1
            if self.neighbors_checked % self.check_neighborhood_print_interval == 0:
                self.log("%d " % self.neighbors_checked, newline=False)
            if self.check_solution(neighbor) is not None:
                self.best_neighbor = neighbor
                if not self.steepest_descent:
                    break
            if self.cpu.total >= self.cpu_limit:
                completed = False
                break
        self.log("<Total %d>" % self.neighbors_checked)
        return completed
        
    def _move_to_best_neighbor(self):
        """Take a step to the next solution on the search path. If the best_neighbor attribute is
        None, it means the local search was unable to find an improving neighbor, and this method 
        will return False. If a best_neighbor exists, the method returns True."""
        if self.best_neighbor is None:
            self.log.warn("no improving neighbor found")
            self.log.info(" --- %s finished --- " % (self.__class__.__name__,))
            return False
        self.current_solution = self.best_neighbor
        self.current_neighbors = iter(self.neighbors(self.current_solution))
        self.neighbors_checked = 0
        self.best_neighbor = None
        return True
        
    def initial_solution(self):
        raise NotImplementedError()
        
    def neighborhood(self, solution):
        raise NotImplementedError()
        
        
        
for state_cls in [Uninitialized, Initialized, Bootstrapped, Running]:
    DFS.add_default_state(state_cls())
    
    
    
def ls(initsol):
    sol = initsol
    while True:
        for neighbor in neighborhood(sol):
            if neighbor < sol:
                best_neighbor = neighbor
                if not steepest_descent:
                    break
        if best_neighbor is None:
            sol = best_neighbor
    return sol

        
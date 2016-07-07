from khronos.opt.localsearch import LocalSearch

class TabuSearch(LocalSearch):
    """A general algorithm intended to be used for implementing Tabu-Search-like algorithms. In 
    addition to the methods required for the LocalSearch class, TabuSearch requires the definition 
    of a select() method, which, given a list of (neighbor, objective) pairs, selects the best 
    neighbor, that is, the solution the search will move to."""
    def _check_neighborhood(self):
        completed = True
        self.log("Checking neighborhood... ", newline=False)
        for neighbor in self.current_neighbors:
            self.neighbors_checked += 1
            if self.neighbors_checked % self.check_neighborhood_print_interval == 0:
                self.log("%d " % self.neighbors_checked, newline=False)
            objective = self.objective(neighbor)
            self.current_neighborhood.append((neighbor, objective))
            if self.check_solution(neighbor, objective) is not None:
                self.best_neighbor = neighbor
                if not self.steepest_descent:
                    break
            if self.cpu.total >= self.cpu_limit:
                completed = False
                break
        self.log("<Total %d>" % self.neighbors_checked)
        if completed and (self.steepest_descent or self.best_neighbor is None):
            self.best_neighbor = self.select(self.current_neighborhood)
        return completed
        
    def _move_to_best_neighbor(self):
        """Take a step to the next solution on the search's path."""
        self.current_neighborhood = []
        return LocalSearch._move_to_best_neighbor(self)
        
    def select(self, neighborhood):
        """Given a list of neighbors and respective objective function values, select the next 
        solution to move to."""
        raise NotImplementedError()
        
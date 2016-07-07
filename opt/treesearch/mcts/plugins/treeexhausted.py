from opt.solver import Solver


class TreeExhausted(Solver.Plugin):
    signal_map = {Solver.SIGNALS.SOLVER_RUNNING: "check",
                  Solver.SIGNALS.ITERATION_FINISHED: "check"}

    def check(self):
        """If the root node has been exhausted, the search is finished."""
        solver = self.solver
        if solver.root.is_exhausted:
            solver.interrupts.add("root node exhausted")
            if solver.termination is None:
                if solver.solutions.feas_count > 0:
                    solver.termination = solver.TERMINATION.OPTIMAL
                else:
                    solver.termination = solver.TERMINATION.INFEASIBLE

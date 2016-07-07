from utils.namespace import Namespace


SIGNALS = Namespace(
    SOLVER_UNINITIALIZING="solver uninitializing",
    SOLVER_UNINITIALIZED="solver uninitialized",
    SOLVER_INITIALIZING="solver initializing",
    SOLVER_INITIALIZED="solver initialized",
    SOLVER_BOOTSTRAPPING="solver bootstrapp,ing",
    SOLVER_BOOTSTRAPPED="solver bootstrappe,d",
    SOLVER_RUNNING="solver running",
    SOLVER_PAUSING="solver pausing",
    SOLVER_PAUSED="solver paused",
    SOLVER_FINISHING="solver fini,shing",
    SOLVER_FINISHED="solver finished",

    INSTANCE_LOADING="instance loading",
    INSTANCE_LOADED="instance loaded",
    INSTANCE_SET="instance set",

    ITERATION_STARTING="iteration starting",
    ITERATION_FINISHED="iteration finished",

    INCUMBENT_CHANGED="incumbent changed",
    BOUND_CHANGED="bound changed",
    GAP_CHANGED="gap changed",

    CHECKING_SOLUTION="checking solution",
    SOLUTION_ADDED="solution added",
    BEST_SOL_ALTERNATIVE="alternative best solution",
    BEST_SOL_VALUE_CHANGED="best solution value changed",
    BEST_FEAS_VALUE_CHANGED="best feasible value changed",
    WORST_FEAS_VALUE_CHANGED="worst feasible value changed",
    LEAST_INFEAS_VALUE_CHANGED="least infeasible value changed",
    MOST_INFEAS_VALUE_CHANGED="most infeasible value changed",

    CPU_LIMIT_REACHED="cpu limit reached",
    ITERATION_LIMIT_REACHED="iteration limit reached",
    SOLUTION_LIMIT_REACHED="solution limit reached",
    GAP_LIMIT_REACHED="gap limit reached",
    KEYBOARD_INTERRUPT="keyboard interrupt",

    UNKNOWN_TERMINATION="unknown termination status",
    OPTIMAL_SOLUTION="optimal solution found",
    PROBLEM_INFEASIBLE="unable to find feasible solutions")

SIGNALS.SOLVER_STATES = [SIGNALS.SOLVER_UNINITIALIZING,
                         SIGNALS.SOLVER_UNINITIALIZED,
                         SIGNALS.SOLVER_INITIALIZING,
                         SIGNALS.SOLVER_INITIALIZED,
                         SIGNALS.SOLVER_BOOTSTRAPPING,
                         SIGNALS.SOLVER_BOOTSTRAPPED,
                         SIGNALS.SOLVER_RUNNING,
                         SIGNALS.SOLVER_PAUSING,
                         SIGNALS.SOLVER_PAUSED,
                         SIGNALS.SOLVER_FINISHING,
                         SIGNALS.SOLVER_FINISHED]

SIGNALS.INSTANCE_EVENTS = [SIGNALS.INSTANCE_LOADING,
                           SIGNALS.INSTANCE_LOADED,
                           SIGNALS.INSTANCE_SET]

SIGNALS.ITERATION_EVENTS = [SIGNALS.ITERATION_STARTING,
                            SIGNALS.ITERATION_FINISHED]

SIGNALS.PROGRESS_EVENTS = [SIGNALS.INCUMBENT_CHANGED,
                           SIGNALS.BOUND_CHANGED,
                           SIGNALS.GAP_CHANGED]

SIGNALS.SOLUTION_LIST_EVENTS = [SIGNALS.CHECKING_SOLUTION,
                                SIGNALS.SOLUTION_ADDED,
                                SIGNALS.BEST_SOL_ALTERNATIVE,
                                SIGNALS.BEST_SOL_VALUE_CHANGED,
                                SIGNALS.BEST_FEAS_VALUE_CHANGED,
                                SIGNALS.WORST_FEAS_VALUE_CHANGED,
                                SIGNALS.LEAST_INFEAS_VALUE_CHANGED,
                                SIGNALS.MOST_INFEAS_VALUE_CHANGED]

SIGNALS.INTERRUPTS = [SIGNALS.CPU_LIMIT_REACHED,
                      SIGNALS.ITERATION_LIMIT_REACHED,
                      SIGNALS.SOLUTION_LIMIT_REACHED,
                      SIGNALS.GAP_LIMIT_REACHED,
                      SIGNALS.KEYBOARD_INTERRUPT]

SIGNALS.TERMINATIONS = [SIGNALS.UNKNOWN_TERMINATION,
                        SIGNALS.OPTIMAL_SOLUTION,
                        SIGNALS.PROBLEM_INFEASIBLE]

SIGNALS.ALL = (SIGNALS.SOLVER_STATES +
               SIGNALS.INSTANCE_EVENTS +
               SIGNALS.ITERATION_EVENTS +
               SIGNALS.PROGRESS_EVENTS +
               SIGNALS.SOLUTION_LIST_EVENTS +
               SIGNALS.INTERRUPTS +
               SIGNALS.TERMINATIONS)

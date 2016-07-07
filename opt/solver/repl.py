from cmd import Cmd


class SolverInteractiveSession(Cmd):
    prompt = "(solver) "

    def __init__(self, solver):
        Cmd.__init__(self)
        self.solver = solver
        self.prompt = "{0} {1} > ".format(self.solver.state, type(self.solver).__name__)

    def do_reset(self):
        self.solver.reset()

    def do_report(self, line):
        print line
        self.solver.report()
        return False

    def do_init(self, line):

        self.solver.init(instance=instance, seed=seed)
        return False

    def do_quit(self, line):
        self.stdout.write("Bye.\n")
        return True

    def postcmd(self, stop, line):
        self.prompt = "{0} {1} >> ".format(self.solver.state.capitalize(),
                                           type(self.solver).__name__)
        return stop

    do_q = do_quit
    do_h = Cmd.do_help

from opt.solver import Solver


class TreeSearchParamSet(Solver.ParamSet):
    pruning = Solver.Param(description="flag indicating whether to use pruning (B&B) or not",
                           options="0/1 or True/False",
                           domain=(False, True),
                           default=False)

    @pruning.adapter
    def pruning(self, flag):
        if isinstance(flag, basestring):
            flag = flag.strip().lower()
        if flag in (True, 1, "1", "t", "true"):
            return True
        if flag in (False, 0, "0", "f", "false"):
            return False
        raise ValueError("unexpected pruning flag value: {!r}".format(flag))

    # --------------------------------------------------------------------------
    root_fnc = Solver.Param(description="function used to create the root node",
                            options="callable taking the solver as only argument",
                            default="root")

    @root_fnc.adapter
    def root_fnc(self, fnc):
        if isinstance(fnc, basestring):
            solver = self.object
            fnc = getattr(solver.Node, fnc)
        return fnc

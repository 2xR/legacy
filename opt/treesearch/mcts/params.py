from utils.interval import Interval
from utils.misc import INF, check_subclass

from opt.solver import Solver
from opt.treesearch import TreeNode

from .metanode import MetaNode


class MCTS_ParamSet(Solver.ParamSet):
    pruning = Solver.Param(description="flag indicating whether to use pruning (B&B) or not",
                           options="0/1 or [T]rue/[F]alse",
                           domain=(False, True),
                           default=False)

    @pruning.adapter
    def pruning(self, flag):
        if isinstance(flag, str):
            flag = flag.strip().lower()
        if flag in (True, 1, "1", "t", "true"):
            return True
        if flag in (False, 0, "0", "f", "false"):
            return False
        raise ValueError("unexpected pruning flag value: {!r}".format(flag))

    @pruning.setter
    def pruning(self, flag):
        solver = self.owner
        try:
            listener = self.__pruning_listener
        except AttributeError:
            def prune_tree():
                root = solver.root
                if root is not None and root.bound is not None:
                    root.prune(solver.incumbent)

            listener = solver.channel.listen(solver.SIGNALS.INCUMBENT_CHANGED, prune_tree)
            self.__pruning_listener = listener
        listener.deployed = flag

    # ------------------------------------------------------------------------------
    node_class = Solver.Param(description="node class used by the solver",
                              options="a subclass of TreeNode",
                              default=None)

    @node_class.adapter
    def node_class(self, cls):
        if cls is None:
            return type(self.owner).Node
        self.verify_node_class_requirements(cls)
        return cls

    @node_class.setter
    def node_class(self, cls):
        solver = self.owner
        solver.log.debug("Setting objective function and sense from node class...")
        solver.sense = cls.sense
        solver.objective = cls.objective

    def verify_node_class_requirements(self, cls):
        check_subclass(cls, TreeNode)
        # solver = self.owner
        # missing = {req for req in solver.node_class_requirements if not req.verify(cls)}
        # if len(missing) > 0:
        #     raise Exception("missing node class requirements: {}"
        #                     .format(", ".join(map(str, missing))))

    # ------------------------------------------------------------------------------
    metanode_class = Solver.Param(description="metanode class used by the solver",
                                  options="a subclass of MetaNode",
                                  default=None)

    @metanode_class.adapter
    def metanode_class(self, cls):
        if cls is None:
            return type(self.owner).MetaNode
        check_subclass(cls, MetaNode)
        return cls

    # ------------------------------------------------------------------------------
    exploration_coeff = Solver.Param(description=("controls balance between exploration"
                                                  " and exploitation in UCT"),
                                     domain=Interval(0.0, INF),
                                     default=1.0)

    @exploration_coeff.adapter
    def exploration_coeff(self, coeff):
        return float(coeff)

    # ------------------------------------------------------------------------------
    expansion_limit = Solver.Param(description=("the maximum number of children "
                                                "created per iteration"),
                                   options="one or more (inf for full expansion)",
                                   domain=Interval(1, INF),
                                   default=1)

    @expansion_limit.adapter
    def expansion_limit(self, limit):
        return float(limit)

    # ------------------------------------------------------------------------------
    selection_policy = Solver.Param(description="node selection policy used",
                                    options="function returning a list of candidate nodes",
                                    default=None)

    @selection_policy.adapter
    def selection_policy(self, fnc):
        solver = self.owner
        if fnc is None:
            return solver.selection_policy
        if isinstance(fnc, str):
            return getattr(solver, fnc)
        if callable(fnc):
            return fnc
        raise Exception("unrecognized selection policy: {!r}".format(fnc))

    # ------------------------------------------------------------------------------
    selection_score_terms = Solver.Param(description=("list of terms used in the node "
                                                      "selection score expression"),
                                         default=["exploration_score", "exploitation_score"])

    @selection_score_terms.adapter
    def selection_score_terms(self, terms):
        """We can pass a list of callables, strings, or a single string."""
        if isinstance(terms, str):
            terms = terms.split()
        solver = self.owner
        actual_terms = []
        for term in terms:
            if isinstance(term, str):
                actual_terms.append(getattr(solver.MetaNode, term))
            elif callable(term):
                actual_terms.append(term)
            else:
                raise ValueError("score terms must be callable or string: {!r}".format(term))
        return actual_terms

    # ------------------------------------------------------------------------------
    simulation_policy = Solver.Param(description="node simulation policy used",
                                     options="function returning a TreeNode or objective value",
                                     default=None)

    @simulation_policy.adapter
    def simulation_policy(self, fnc):
        solver = self.owner
        if fnc is None:
            return solver.simulation_policy
        if isinstance(fnc, str):
            return getattr(solver, fnc)
        if callable(fnc):
            return fnc
        raise Exception("unrecognized selection policy: {!r}".format(fnc))


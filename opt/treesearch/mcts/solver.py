from copy import deepcopy
from itertools import izip

from utils.misc import max_elems
from opt.solver import Solver
from opt.treesearch.node import TreeNode
from opt.solver.status import Field

from .metanode import MetaNode
from .params import MCTS_ParamSet
from .plugins.treeexhausted import TreeExhausted


def extract_treedims(solver):
    root = solver.root
    return "- / -" if root is None else "{} / {}".format(root.size, root.height)


Field.TreeDims = Field(header="Nodes / Height",
                       width=18,
                       align=str.center,
                       extract=extract_treedims)


class MCTS(Solver):
    """
    A generic Monte-Carlo Tree Search solver. In most cases, this should work seamlessly with
    existing TreeNode subclasses. For more advanced usage, MetaNode can be subclassed and
    used (through the 'metanode_class' parameter) instead of the default meta-node class.
    """
    SIGNALS = deepcopy(Solver.SIGNALS)
    SIGNALS.PRUNING_NODE = "pruning node"
    SIGNALS.ALL.append(SIGNALS.PRUNING_NODE)

    ParamSet = MCTS_ParamSet  # paramset class used by this solver
    Node = TreeNode           # node class used by default
    MetaNode = MetaNode       # reference to base metanode class
    default_plugins = list(Solver.default_plugins) + [TreeExhausted]

    def __init__(self, **params):
        Solver.__init__(self, **params)
        self.status.fields.append(Field.TreeDims)
        self.root = None

    def _extract_solution_and_meta(self, sol_container):
        if isinstance(sol_container, TreeNode):
            return sol_container.solution_and_meta()
        else:
            return sol_container, {}

    def _reset(self):
        self.root = None

    def _bootstrap(self):
        """Bootstrap the search by creating the root node and running a simulation from it."""
        root_node = self.params.node_class.root(self)
        root_meta = self.params.metanode_class(self, root_node)
        self.root = root_meta
        if root_meta.is_exhausted:
            self.solutions.check(root_node)
        else:
            is_better = self.sense.is_better
            if root_meta.bound is not None and is_better(self.bound, root_meta.bound.value):
                self.bound = root_meta.bound.value
            sim_results = self._simulation_step([root_meta])
            self._backpropagation_step([root_meta], sim_results)

    def _iterate(self):
        """An iteration of MCTS consists of four steps:
            1) selection of a non-fully expanded node in the tree
            2) expansion of one or more children of the selected node
            3) for each new node, run a random simulation until a terminal state is reached
            4) use the results of the simulations to update the statistics of the selected node
               and its ancestors
        """
        selected = self._selection_step()
        expanded = self._expansion_step(selected)
        if len(expanded) > 0:
            sim_results = self._simulation_step(expanded)
            self._backpropagation_step(expanded, sim_results)

    def _selection_step(self):
        """Descend through the tree until we find an expandable node (i.e. a node which hasn't
        been fully expanded yet).  This step uses a selection policy that, given a list of
        metanodes, should return a list of candidates that are considered best according to some
        criterion.  The default criterion is to maximize the score in a UCT-like formula."""
        selection_policy = self.params.selection_policy
        random_choice = self.rng.choice
        metanode = self.root
        while not metanode.is_expandable:
            children = metanode.children
            if len(children) == 1:
                metanode = children[0]
            else:
                candidates = selection_policy(children)
                if len(candidates) == 1:
                    metanode = candidates[0]
                else:
                    metanode = random_choice(candidates)
        return metanode

    def selection_policy(self, metanodes):
        terms = self.params.selection_score_terms
        return max_elems(metanodes, key=lambda m: sum(term(m) for term in terms))

    def _expansion_step(self, selected):
        expanded = []
        count = 0
        while count < self.params.expansion_limit:
            child = selected.create_next_child()
            if child is not None:
                selected.add_child(child)
                expanded.append(child)
            if not selected.branches.advance():
                break
            count += 1
        return expanded

    def _simulation_step(self, expanded):
        sim_policy = self.params.simulation_policy
        return [sim_policy(metanode) for metanode in expanded]

    def simulation_policy(self, metanode):
        return metanode.node.simulation()

    def _backpropagation_step(self, expanded, sim_results):
        for metanode, sim_result in izip(expanded, sim_results):
            if isinstance(sim_result, TreeNode):
                self.solutions.check(sim_result)
                metanode.stats.set_sim_result(self.objective(sim_result))
            else:
                metanode.stats.set_sim_result(sim_result)

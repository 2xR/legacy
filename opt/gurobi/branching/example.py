from __future__ import absolute_import

import random
from gurobipy import Model, quicksum, GRB

from utils.misc import check_subclass
from opt.treesearch.mcts import MCTS
from opt.gurobi import branching


def new_model(nplants, nwarehouses, seed=None):
    data = generate_data(nplants, nwarehouses, seed)
    return build_model(*data)


def generate_data(nplants, nwarehouses, seed=None):
    if seed is not None:
        random.seed(seed)
    plants = range(nplants)
    warehouses = range(nwarehouses)
    demand = [random.randint(10, 20) for _ in warehouses]
    capacity = [random.randint(15, 25) for _ in plants]
    fixed_costs = [random.randint(10, 20) * 1000 for _ in plants]
    trans_costs = [[random.randint(10, 50) * 1000 for _ in plants] for _ in warehouses]
    return plants, warehouses, capacity, demand, fixed_costs, trans_costs


def build_model(plants, warehouses, capacity, demand, fixed_costs, trans_costs):
    # decision variables
    m = Model("facility")
    is_open = []
    for p in plants:
        is_open.append(m.addVar(vtype=GRB.BINARY,
                                name="is_open[{}]".format(p)))
    trans_qty = []
    for w in warehouses:
        trans_qty.append([])
        for p in plants:
            trans_qty[w].append(m.addVar(vtype=GRB.CONTINUOUS,
                                         name="trans_qty[{}.{}]".format(p, w),
                                         lb=0.0))
    m.update()
    # objective function
    m.setObjective(quicksum(fixed_costs[p] * is_open[p]
                            for p in plants) +
                   quicksum(trans_costs[w][p] * trans_qty[w][p]
                            for w in warehouses
                            for p in plants),
                   GRB.MINIMIZE)
    # constraints
    for p in plants:
        m.addConstr(quicksum(trans_qty[w][p] for w in warehouses) <= capacity[p] * is_open[p],
                    "Capacity({})".format(p))
    for w in warehouses:
        m.addConstr(quicksum(trans_qty[w][p] for p in plants) == demand[w],
                    "Demand({})".format(w))
    m.update()
    return m


class MipMCTS(MCTS):
    def __init__(self, **params):
        MCTS.__init__(self, **params)

        def set_sense_from_instance():
            self.sense = min if self.instance.model_sense == GRB.MINIMIZE else max

        self.channel.listen(self.SIGNALS.INSTANCE_SET, set_sense_from_instance)

    class ParamSet(MCTS.ParamSet):
        class Defaults(MCTS.ParamSet.Defaults):
            pruning = True
            expansion_limit = 2
            selection_score_terms = ["exploration_score", "bound_score"]

        branching_rule = MCTS.Param(description="branching rule used by MCTS",
                                    options=", ".join(branching.__all__),
                                    default=branching.RandomBranching)

        @branching_rule.adapter
        def branching_rule(self, rule):
            if isinstance(rule, str):
                rule = getattr(branching, rule)
            if isinstance(rule, branching.BranchingRule):
                return rule
            elif isinstance(rule, type):
                check_subclass(rule, branching.BranchingRule)
                return rule()
            elif callable(rule):
                return rule()
            raise TypeError("unrecognized branching rule: {!r}".format(rule))

    class Node(MCTS.Node):
        def __init__(self, solver, data):
            self.solver = solver
            self.data = data

        @classmethod
        def root(cls, solver):
            return cls(solver, solver.params.branching_rule.root(solver.instance))

        def branches(self):
            cls = type(self)
            solver = self.solver
            var_name, children = solver.params.branching_rule.branches(self.data, rng=solver.rng)
            return [cls(solver, data) for data in children if data.relax_sol is not None]

        def is_leaf(self):
            return len(self.data.fractional_vars) == 0

        sense = min

        def objective(self):
            return self.data.relax_obj

        def bound(self):
            return self.data.relax_obj

        def simulation(self):
            return self.data.relax_obj

        def solution_and_meta(self):
            return self.data.relax_sol, {}

    class MetaNode(MCTS.MetaNode):
        def release_node(self):
            pass

        def bound_score(self):
            return 2.0 / (1.0 + abs(self.bound.value - self.solver.bound))


def main(model, mcts=None):
    if mcts is None:
        mcts = MipMCTS()
    meta = {}
    for rule in [branching.PseudocostBranching(),
                 branching.StrongBranching(cand_lookahead=5),
                 branching.ReliabilityBranching(cand_lookahead=5, min_reliability=1)]:
        mcts.reset()
        mcts.solve(model, seed=0, cpu_limit=60.0, branching_rule=rule)
        meta[rule] = dict(cpu=mcts.cpu.total,
                          iters=mcts.iters.total,
                          incumbent=mcts.incumbent,
                          bound=mcts.bound,
                          gap=mcts.gap)
    return meta


model = new_model(40, 20, seed=0)
mcts = MipMCTS()

if __name__ == "__main__":
    from pprint import pprint

    results = main(model, mcts)
    pprint(results)

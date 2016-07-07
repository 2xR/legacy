from sys import stdout

from utils.prettyrepr import prettify_class
from utils.misc import INF

from opt.infeasible import Infeasible


@prettify_class
class MetaNodeStats(object):
    __slots__ = ("metanode",         # reference to the owner metanode
                 "sim_count",        # number of simulations run under this node
                 "sim_result",       # result of the simulation run from this node
                 "sim_best_result")  # result of the best simulation run under this node

    def __init__(self, metanode):
        self.metanode = metanode
        self.sim_count = 0
        self.sim_result = None
        self.sim_best_result = Infeasible(INF)

    def __info__(self):
        z = self.format_sim_result(self.sim_result)
        z_star = self.format_sim_result(self.sim_best_result)
        return "{} sims, z={}, z*={}".format(self.sim_count, z, z_star)

    @staticmethod
    def format_sim_result(sim_result):
        """Auxiliary function used by __info__() and report()."""
        if sim_result is None:
            return "undef"
        elif isinstance(sim_result, Infeasible):
            return "infeas({:.03f})".format(sim_result)
        else:
            return "{:.03f}".format(sim_result)

    def set_sim_result(self, sim_result):
        """Set the simulation result of this metanode.  The result is set and propagated up the
        tree, updating the statistics of all metanodes in the path to the root."""
        if self.sim_count != 0:
            raise Exception("erroneous attempt to set simulation result")
        self.sim_count = 1
        self.sim_result = sim_result
        self.sim_best_result = sim_result
        parent = self.metanode.parent
        if parent is not None:
            parent.stats.add_sim_result(sim_result)

    def add_sim_result(self, sim_result):
        """Add a new simulation result (from a child node) to the statistics."""
        metanode = self.metanode
        is_better = metanode.solver.sense.is_better
        while metanode is not None:
            stats = metanode.stats
            if is_better(sim_result, stats.sim_best_result):
                stats.sim_best_result = sim_result
            else:
                break
            metanode = metanode.parent
        self.add_sim_count(+1)

    def remove_sim_result(self, sim_result):
        """Removing a result (from a child) means subtracting a result which has been previously
        added."""
        self.discard_sim_result(sim_result)
        self.add_sim_count(-1)

    def discard_sim_result(self, sim_result):
        """Discarding differs from removing in that the result is not "subtracted" from the
        accumulated statistics.  Instead, this is used to merely indicate that the argument
        result may no longer be reached in this subtree (at least until a new simulation
        produces the same result).  If the result was previously added, use remove_sim_result()
        instead."""
        metanode = self.metanode
        is_better = metanode.solver.sense.is_better
        while metanode is not None:
            stats = metanode.stats
            if sim_result == stats.sim_result:
                stats.add_sim_count(-1)
                stats.sim_result = None
            if sim_result == stats.sim_best_result:
                best = Infeasible(INF)
                if stats.sim_result is not None:
                    best = stats.sim_result
                for child in metanode.children:
                    child_best = child.stats.sim_best_result
                    if is_better(child_best, best):
                        best = child_best
                stats.sim_best_result = best
            metanode = metanode.parent

    def add_sim_count(self, count):
        """Add the argument 'count' to the simulation count of this metanode's stats."""
        self.sim_count += count
        metanode = self.metanode.parent
        while metanode is not None:
            metanode.stats.sim_count += count
            metanode = metanode.parent

    # ------------------------------------------------------------------------------
    def validate(self):
        # verify that the best sim result is indeed the best among the
        # metanode's own simulation and its children's best simulations
        results = [c.stats.sim_best_result for c in self.metanode.children]
        results.append(Infeasible(INF) if self.sim_result is None else self.sim_result)
        assert self.sim_best_result == self.metanode.solver.sense.best_in(results)

        # the total simulation count at self should be equal to the sum of the simulations
        # done by its children plus 1 if self's own simulation hasn't been discarded yet
        own_sim = int(self.sim_result is not None)
        assert self.sim_count - own_sim == sum(c.stats.sim_count for c in self.metanode.children)

        # verify if all children are correctly linked to the parent
        assert all(child.parent is self.metanode for child in self.metanode.children)

    def report(self, indent=0, ostream=stdout):
        z = self.format_sim_result(self.sim_result)
        z_star = self.format_sim_result(self.sim_best_result)
        metanode = self.metanode
        parts = ["  " * indent,
                 "depth={}".format(metanode.depth),
                 "  z={}".format(z),
                 "  z*={}".format(z_star),
                 "  sims={}".format(self.sim_count)]
        if metanode.parent is not None:
            score_terms = [term(metanode) for term in
                           metanode.solver.params.selection_score_terms]
            score = sum(score_terms)
            terms = "".join("{:+.03f}".format(term) for term in score_terms)
            parts.append("  score={:.03f} ({})".format(score, terms))
        parts.append("\n")
        ostream.write("".join(parts))

from math import log, sqrt
from utils.misc import INF
from opt import Infeasible


def exploration_score(metanode):
    if metanode.stats.sim_count == 0:
        return INF
    return (metanode.solver.params.exploration_coeff *
            sqrt(2.0 * log(metanode.parent.stats.sim_count) / metanode.stats.sim_count))


def exploitation_score(metanode):
    sim_best_result = metanode.stats.sim_best_result
    if isinstance(sim_best_result, Infeasible):
        return 0.0
    solutions = metanode.solver.solutions
    z_star = solutions.best_feas_value
    w_star = solutions.worst_feas_value
    if z_star == w_star:
        return 0.0
    return abs(sim_best_result - w_star) / abs(z_star - w_star)


# def exploitation_score_exponential(reward):
#     """Exploitation score functions take a raw linear reward in [0, 1], and should return the
#     exploitation score associated with that reward. The exploitation score should ideally also
#     be in [0, 1]. Use values outside this range with caution!"""
#     return (exp(reward) - 1.0) / (e - 1.0)


# def exploitation_score_linear(reward):
#     """See exploitation_score_exponential()."""
#     return reward


# def infeasibility_penalties(self):
#     """Score term for penalizing failed simulations."""
#     max_infeas = self.solver.max_infeas.degree
#     min_infeas = self.solver.min_infeas.degree
#     delta_infeas = max_infeas - min_infeas
#     if delta_infeas == 0.0:
#         if self.sim_count == self.sim_fails:
#             return [0.0] * len(self.children)
#         return [-c.sim_fails / c.sim_count for c in self.children]
#     penalties = []
#     for child in self.children:
#         z_child = child.sim_best_score
#         if isinstance(z_child, Infeasible):
#             feas_score = (max_infeas - z_child.degree) / delta_infeas
#             penalties.append((feas_score - 1.0) * child.sim_fails / child.sim_count)
#         else:
#             penalties.append(0.0)
#     return penalties

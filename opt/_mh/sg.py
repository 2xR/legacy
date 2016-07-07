from math import exp, log
import random

from khronos.utils import INF, Namespace, biased_choice
from khronos.utils.simplemath import confine


def identity(x):
    """This function is used as the default heuristic function for the semigreedy class."""
    return x


def default_cut(min_score, max_score, greediness):
    """Default function used to calculate the cut score, based on the minimum and maximum
    scores, and the greediness value."""
    return min_score + greediness * (max_score - min_score)


# --------------------------------------------
# BIAS FUNCTIONS
def logarithmic_bias(rank):
    return 1.0 / log(rank + 1.0)


def linear_bias(rank):
    return 1.0 / rank


def polynomial_bias(degree):
    def bias_fnc(rank):
        return 1.0 / (rank ** degree)
    bias_fnc.__name__ = "poly_bias(%d)" % (degree,)
    return bias_fnc


def exponential_bias(rank):
    return 1.0 / exp(rank)


def uniform_bias(rank):
    return 1.0

bias = Namespace(logarithmic=logarithmic_bias,
                 linear=linear_bias,
                 polynomial=polynomial_bias,
                 exponential=exponential_bias,
                 uniform=uniform_bias)


class SemiGreedy(object):
    """Semi-greedy template. Can be used to create restricted candidate lists using cardinality
    and value-based schemes. Also, a bias function may be used to choose an element from the RCL.
    Attributes:
        heuristic - A heuristic function, giving the greedy heuristic function value of an item.
        bias - A bias function, which returns a bias value of a given rank. The bias is used to
            calculate the probability of a candidate being selected from a RCL. The default bias
            function gives the same (non-zero) bias to all ranks, resulting in a random choice
            from the candidate list. The probability of an RCL element x being chosen is given by
                bias(x) / sum(bias(y) for y in RCL)
        cut - A function to calculate the cut score, given the minimum and maximum scores, and a
            greediness value.
        rng - The pseudo random number generator that is used for candidate selection.
    """
    def __init__(self, heuristic=identity, bias=uniform_bias, cut=default_cut, rng=random):
        self.heuristic = heuristic
        self.bias = bias
        self.cut = cut
        self.rng = rng

    def RCL(self, items, greediness=1.0,
            min_ranks=1, max_ranks=INF,
            min_elements=1, max_elements=INF):
        """Build a restricted candidate list from the provided list of items. The cardinality
        arguments 'min_elements' and 'max_elements' are always respected, except when the item
        list does not have enough elements to fulfill the request. If during construction of the
        RCL, the 'min_elements' constraint has been met, and the score of the next item to be
        considered is less than the cut score (explained next), the element is not added and the
        RCL is returned.
        The 'min_ranks' and 'max_ranks' arguments offer a different way to restrict the RCL,
        making it contain, if possible, a number of ranks (different, decreasing scores) between
        'min_ranks' and 'max_ranks'. For instance, if max_ranks is 1, only the first ranked
        elements may enter the RCL, and if max_ranks is 2, only the elements with first and
        second rank are allowed into the RCL.
        The cut score is the minimum score that will be accepted into the RCL after the
        'min_elements' and 'min_ranks' constraints have been met (once again, if possible). It is
        calculated using the cut function, which takes the minimum and maximum scores of the
        provided list of items, and the specified greediness value.
        The return value of this method is a restricted candidate list, consisting of a list of
        (item, score, rank) tuples, where item is an element of the 'items' list, score is its
        corresponding heuristic score, and rank is the position occupied by the item in the
        ranking, e.g. 1 represents the highest score, 5 represents the fifth score, etc."""
        scored_items = sorted((self.heuristic(item), self.rng.random(), item) for item in items)
        # Calculate the cut value, i.e. the minimum score that will be accepted into the RCL.
        min_score = scored_items[0][0]
        max_score = scored_items[-1][0]
        cut_score = self.cut(min_score, max_score, greediness)
        # Set correct limits for the number of elements in the RCL.
        min_elements = confine(min_elements, 1, len(scored_items))
        max_elements = confine(max_elements, min_elements, len(scored_items))
        # Construction main loop. The RCL will consist of all elements whose score is >=
        # than the cut score, calculated using the specified greediness value. The
        # specified minimum number of elements and ranks must be in the RCL before
        # score cutting starts to be checked, i.e. if the RCL still doesn't have
        # 'min_elements' elements and 'min_ranks' ranks, new elements will be added
        # even if their score is less than the cut score.
        RCL = []
        elements = 0
        rank = 1
        last_score = max_score
        while elements < max_elements:
            score, _, item = scored_items.pop()
            if elements >= min_elements and rank >= min_ranks and score < cut_score:
                break
            if score < last_score:
                last_score = score
                rank += 1
                if rank > max_ranks:
                    break
            RCL.append((item, score, rank))
            elements += 1
        return RCL

    def select(self, items, greediness=1.0,
               min_ranks=1, max_ranks=INF,
               min_elements=1, max_elements=INF):
        """Build a RCL and select one random element from it using the specified bias method."""
        RCL = self.RCL(items, greediness, min_ranks, max_ranks, min_elements, max_elements)
        biases = [self.bias(rank) for _, _, rank in RCL]
        return biased_choice(RCL, biases, self.rng)[0]

from __future__ import absolute_import
import random


def biased_choice(biases, rng=random):
    """Randomly pick an integer index using different probabilities for selecting each index. The
    list 'biases' should contain the bias (or weight) of each index in the random draw. Biases
    should be non-negative real numbers of any magnitude. The probability of each index is the
    quotient between its bias and the sum of all biases."""
    assert all(bias >= 0.0 for bias in biases)
    X = rng.uniform(0.0, sum(biases))
    Y = 0.0
    for index, bias in enumerate(biases):
        Y += bias
        if Y >= X:
            return index
    raise Exception("They came from behind!!! We're not supposed to be here... really...")


def sample_filter(predicates, default_tries=10, name=None, doc=None):
    """Given one or more predicates, returns a sampling wrapper function that, passed a
    callable generator of values from a distribution, and optional args and kwargs to that
    callable, generates values from the distribution until all the condition functions return
    True for a particular observation from the distribution. This can be used, e.g. to filter
    out negative values from a Gaussian distribution, like so:
        fltr = sample_filter(lambda x: x > 0)  # only accepts non-negative values

    Then, we apply the sample filter above to the Guassian distribution of the Random class from
    Python's standard library:
        rng = Random(seed)
        value = fltr(rng.gauss, 0, 1)  # -> returns a non-negative observation
        print value
    """
    if not isinstance(predicates, (tuple, list)):
        acceptable = predicates
    else:
        if len(predicates) == 0:
            raise Exception("no predicates provided. invalid sampling filter")
        if len(predicates) == 1:
            acceptable = predicates[0]
        else:
            acceptable = lambda x: all(predicate(x) for predicate in predicates)

    def sample_filter_func(distr, *args, **kwargs):
        """distr is a callable, args and kwargs are passed to distr() to obtain observations from
        the given distribution. If a 'tries' keyword argument is specified, it provides a limit
        for the number of attempts before the sampling filter fails (iff the specified condition
        is not satisfied before the limit is reached). ValueError is raised on failure."""
        # extract the maximum number of samples to try
        tries = kwargs.pop("tries", default_tries)
        for _ in xrange(tries):
            # sample a value, check condition, and repeat until necessary
            value = distr(*args, **kwargs)
            if acceptable(value):
                return value
        raise ValueError("unable to obtain valid observation in %d tries" % tries)

    if name is not None:
        sample_filter_func.__name__ = name
    if doc is not None:
        sample_filter_func.__doc__ = doc
    return sample_filter_func


sample_filter.pos = sample_filter(lambda x: x > 0, name="sample_filter.pos")
sample_filter.neg = sample_filter(lambda x: x < 0, name="sample_filter.neg")
sample_filter.nonpos = sample_filter(lambda x: x <= 0, name="sample_filter.nonpos")
sample_filter.nonneg = sample_filter(lambda x: x >= 0, name="sample_filter.nonneg")

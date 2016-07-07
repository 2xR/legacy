from __future__ import absolute_import
from math import sqrt, factorial


# *Very important* constants (special enough to break the all-uppercase constant convention)
Inf = Infinity = float("Inf")
NaN = float("NaN")


# --------------------------------------------------------------------------------------------------
# Simple miscellaneous functions
# --------------------------------------------------------------------------------------------------
def sign(x):
    """Returns the sign of the argument as (+1, -1, 0) for (>0, <0, =0) respectively."""
    return +1 if x > 0 else -1 if x < 0 else 0


def clamp(value, minimum, maximum):
    """Clamp a value using the interval [minimum, maximum]."""
    return min(maximum, max(minimum, value))


def product(sequence, start=1):
    """Computes the product of a sequence of numbers. Like in the builtin sum(), 'start' may be
    provided as the initial value of the product."""
    p = start
    for x in sequence:
        p *= x
    return p


def solve_quadratic(a, b, c):
    """Solve the quadratic equation aX**2 + bX + c = 0. Returns the two possible values of X."""
    d = sqrt(b*b - 4*a*c)
    x0 = float(-b - d) / (2.0 * a)
    x1 = float(-b + d) / (2.0 * a)
    return x0, x1


def linear_least_squares(points):
    """An implementation of the least-squares method for finding the best linear function
    approximation for a set of points (an iterable containing (x, y) tuples). This method returns
    the constants 'a' and 'b' in the equation y = ax + b."""
    n = 0
    sum_x = 0.0
    sum_y = 0.0
    sum_xx = 0.0
    sum_xy = 0.0
    for x, y in points:
        n += 1
        sum_x += x
        sum_y += y
        sum_xx += x ** 2
        sum_xy += x * y
    a = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x ** 2)
    b = (sum_xx * sum_y - sum_x * sum_xy) / (n * sum_xx - sum_x ** 2)
    return a, b


# --------------------------------------------------------------------------------------------------
# Simple combinatorics functions
# --------------------------------------------------------------------------------------------------
def permutations(n, r=None):
    """Computes the number of permutations from a set of 'n' elements."""
    if r is None:
        r = n
    return product(xrange(n-r+1, n+1))


def combinations(n, k):
    """Computes the number of 'k'-combinations from a set of 'n' elements."""
    return permutations(n, k) / factorial(k)


# --------------------------------------------------------------------------------------------------
# Basic descriptive statistics
# --------------------------------------------------------------------------------------------------
def geometric_mean(values):
    """Compute the geometric mean from 'values'."""
    prod = 1
    count = 0.0
    for value in values:
        prod *= value
        count += 1.0
    return prod ** (1.0 / count)


def mean(values):
    """Compute the arithmetic mean from 'values'."""
    total = 0
    count = 0.0
    for value in values:
        total += value
        count += 1.0
    return total / count


def variance(values, mu=None, bessel_correction=False):
    """Compute the variance of the sample given by 'values'.

    ALIAS: var()
    """
    if mu is None:
        mu = mean(values)
    n = len(values) - (1 if bessel_correction else 0)
    return float(sum((mu - x)**2 for x in values)) / n

var = variance


def standard_deviation(values, mu=None, bessel_correction=False):
    """Compute the standard deviation of the sample given by 'values'.

    ALIAS: stddev()
    """
    return sqrt(variance(values, mu, bessel_correction))

stddev = standard_deviation


def zscore(x, mu, sigma):
    """The z-score or standard score of a value x is equal to its (signed) deviation from the
    mean normalized by the standard deviation, i.e. it represents the number of standard
    deviations that x is above the mean. A negative z-score indicates that the value is below the
    mean. """
    return float(x - mu) / sigma


def default_quantile_index(p, n):
    """Default quantile index method. Given 'p' and 'n', it returns the zero-based index where
    the 'p'-quantile is located in a population of size 'n'. """
    return p * (n-1)


def quantile(p, values, method=default_quantile_index):
    """Quantile calculation for a given *sorted sequence* of real numbers. It is important that
    'values' is a sorted sequence, otherwise this function will produce incorrect results. The
    quantile argument 'p' must belong to the interval [0, 1].

    Note that there are several different methods to estimate quantiles. Please refer to wikipedia
    for detailed information:
        http://en.wikipedia.org/wiki/Quantile#Estimating_the_quantiles_of_a_population

    The user can specify the quantile estimation method to use by passing the 'method' argument.
    'method' should be a function taking two arguments, 'p' (the quantile being estimated) and
    'n' (the size of the population), and should return a real number 'i' indicating the index of
    the element where the given quantile is located. If 'i' is an integer value, the 'p'-quantile
    is given by 'values[i]'. If 'i' is a fractional number, then a simple linear interpolation is
    done between 'values[floor(i)]' and 'values[ceil(i)]'. The default method directly maps 'p'
    into indices of the population between 0 and n-1 using the formula 'i = p * (n-1)'. """
    if not 0.0 <= p <= 1.0:
        raise ValueError("quantile must lie in [0, 1]")
    n = len(values)
    index = method(p, n)
    i, j = divmod(index, 1.0)
    i = int(i)
    if i == n - 1:
        assert j == 0.0
        return float(values[i])
    return values[i] * (1.0 - j) + values[i+1] * j


def median(values, method=default_quantile_index):
    """The median is simply a special case of the quantile statistic."""
    return quantile(0.5, values, method)

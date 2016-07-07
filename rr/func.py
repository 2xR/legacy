"""
Additional tools for functional-style programming in Python.
"""
from __future__ import absolute_import
import functools
import operator


# We rebind 'map', 'reduce', 'filter', 'apply' and 'partial' here just so that these functions
# can be used in the same manner as the functions actually defined in this module e.g.
# func.apply(f, [2, 3])
map = map
reduce = reduce
filter = filter
apply = apply
partial = functools.partial


def pipe(*funcs, **kwargs):
    """Create a pipeline of functions. The first function is passed the original arguments, and
    the remaining functions take as single argument the return value of the previous function.
        func.pipe(f, g, ...) <==> ...(g(f(x)))

    The name and docstring of the newly created function can be given through the 'name' and
    'doc' keyword arguments.
    """
    def pipe_func(*args, **kwargs):
        ifuncs = iter(pipe_func.funcs)
        result = next(ifuncs)(*args, **kwargs)
        for func in ifuncs:
            result = func(result)
        return result
    pipe_func.funcs = list(funcs)
    if "name" in kwargs:
        pipe_func.__name__ = kwargs["name"]
    if "doc" in kwargs:
        pipe_func.__doc__ = kwargs["doc"]
    return pipe_func


def star_pipe(*funcs, **kwargs):
    """Like pipe(), but when arguments are passed *between* functions in the pipeline, the result
    of the previous function is expanded as star arguments (*args). Note that this will raise a
    TypeError if these intermediate return values are not all iterable.
        func.pipe(f, g, ...) <==> ...(*g(*f(x)))

    The name and docstring of the newly created function can be given through the 'name' and
    'doc' keyword arguments.
    """
    def star_pipe_func(*args, **kwargs):
        ifuncs = iter(star_pipe_func.funcs)
        result = next(ifuncs)(*args, **kwargs)
        for func in ifuncs:
            result = func(*result)
        return result
    star_pipe_func.funcs = list(funcs)
    if "name" in kwargs:
        star_pipe_func.__name__ = kwargs["name"]
    if "doc" in kwargs:
        star_pipe_func.__doc__ = kwargs["doc"]
    return star_pipe_func


def tee(*funcs, **kwargs):
    """Create a function which broadcasts all arguments it receives to a list of "sub-functions".
    The return value of the tee function is a list with the return values of the individual sub-
    functions.
        func.tee(f, g, ...)(x) <==> [f(x), g(x), ...]

    The name and docstring of the newly created function can be given through the 'name' and
    'doc' keyword arguments.
    """
    def tee_func(*args, **kwargs):
        return [func(*args, **kwargs) for func in tee_func.funcs]
    tee_func.funcs = list(funcs)
    if "name" in kwargs:
        tee_func.__name__ = kwargs["name"]
    if "doc" in kwargs:
        tee_func.__doc__ = kwargs["doc"]
    return tee_func


def _op_reduce(op):
    """Internal function. Creates a function which calls a number of sub-functions using tee(),
    then merges the results of the sub-functions using reduce() with the argument 'op'.
    Then end result is, for example, with op=operator.add, the function will compute the sum of
    the results of the sub-functions.
        _op_reduce(op)(f, g, ...)(x) <==> reduce(op, [F(x) for F in [f, g, ...]])
    """
    def op_reduce_func(*funcs, **kwargs):
        return pipe(tee(*funcs), partial(reduce, op), **kwargs)
    return op_reduce_func


add = _op_reduce(operator.add)
sub = _op_reduce(operator.sub)
mul = _op_reduce(operator.mul)
div = _op_reduce(operator.div)
floordiv = _op_reduce(operator.floordiv)
truediv = _op_reduce(operator.truediv)
mod = _op_reduce(operator.mod)
pow = _op_reduce(operator.pow)

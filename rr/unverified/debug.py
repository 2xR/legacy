import warnings
import functools
from sys import stdout


def wrap(func, ostream=stdout):
    """Function decorator. Prints the arguments and return value of the wrapped function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        wrap.debug_call_count += 1
        wrap.debug_call_depth += 1
        call_count = wrap.debug_call_count
        call_depth = wrap.debug_call_depth
        ostream.write("#%d depth=%d CALL: %s() <-- %s, %s\n" %
                      (call_count, call_depth, func.__name__, args, kwargs))
        result = func(*args, **kwargs)
        ostream.write("#%d depth=%d RETURN: %s() --> %s\n" %
                      (call_count, call_depth, func.__name__, result))
        wrap.debug_call_depth -= 1
        return result
    return wrapper

wrap.debug_call_count = 0
wrap.debug_call_depth = 0


def deprecated(func):
    """"This is a decorator which can be used to mark functions as deprecated. It will result in
    a warning being emitted when the function is used."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        warnings.warn_explicit("Call to deprecated function %s()" % func.__name__,
                               category=DeprecationWarning,
                               filename=func.func_code.co_filename,
                               lineno=func.func_code.co_firstlineno+1)
        return func(*args, **kwargs)
    return wrapper


def try_map(fnc, iterable, exceptions=Exception):
    """Call 'fnc' on each element of 'iterable' and catch all 'exceptions'.
    This function returns two lists:
        - the first list contains (elem, value) pairs where 'value' is the result of 'fnc(elem)'
        - the second list contains (elem, error) pairs, where 'error' is the exception raised by
            calling 'fnc(elem)'
    """
    elem_value = []
    elem_error = []
    for elem in iterable:
        try:
            value = fnc(elem)
        except exceptions as error:
            elem_error.append((elem, error))
        else:
            elem_value.append((elem, value))
    return elem_value, elem_error


def try_calls(fncs, exceptions=Exception):
    """Call all functions in 'fncs' and catch all 'exceptions'. This function returns two lists:
        - the first list contains (fnc, result) pairs, where 'result' is the result of 'fnc()'
        - the second list contains (fnc, error) pairs, where 'error' is the exception raised by
            calling 'fnc()'
    """
    fnc_result = []
    fnc_error = []
    for fnc in fncs:
        try:
            result = fnc()
        except exceptions as error:
            fnc_error.append((fnc, error))
        else:
            fnc_result.append((fnc, result))
    return fnc_result, fnc_error

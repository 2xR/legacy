"""
This module contains a bunch of functions to make it more bearable to write grammars in BNF.
The functions in this module are meant to be used with PLY (Python Lex Yacc).
"""
import inspect


def caller_locals():
    """Gets the locals dictionary of the caller of this function's caller."""
    return inspect.stack()[2][0].f_locals


def add_production(production, owner):
    print("Adding {}...".format(production.__name__))
    owner[production.__name__] = production


def repeat_exactly(n, elem_name, list_name=None, owner=None):
    """Creates a BNF rule that puts in a list an exact number of consecutive occurrences of a
    given symbol (terminal or non-terminal)."""
    if list_name is None:
        list_name = "{0}s".format(elem_name)
    if owner is None:
        owner = caller_locals()

    def rule(p):
        """
        {0} : {1}
        """.format(list_name, elem_name*n)
        p[0] = [p[i] for i in xrange(1, n+1)]

    rule.__name__ = "p_{0}_{1}".format(list_name, n)
    add_production(rule, owner)


def repeat_at_least(n, elem_name, list_name=None, owner=None):
    if list_name is None:
        list_name = "{0}s".format(elem_name)
    if owner is None:
        owner = caller_locals()
    repeat_exactly(n, elem_name, list_name, owner)

    def append(p):
        """
        {0} : {0} {1}
        """.format(list_name, elem_name)
        p[1].append(p[2])
        p[0] = p[1]

    append.__name__ = "p_{0}_append".format(list_name)
    add_production(append, owner)


def repeat_between(min, max, elem_name, list_name=None, owner=None):
    if list_name is None:
        list_name = "{0}s".format(elem_name)
    if owner is None:
        owner = caller_locals()
    for n in xrange(min, max+1):
        repeat_exactly(n, elem_name, list_name, owner)


def repeat(elem_name, list_name=None, min=0, max=None, owner=None):
    if list_name is None:
        list_name = "{0}s".format(elem_name)
    if owner is None:
        owner = caller_locals()
    if max is None:
        repeat_at_least(min, elem_name, list_name, owner)
    else:
        repeat_between(min, max, elem_name, list_name, owner)

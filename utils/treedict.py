"""This module provides some functions for creating and managing dictionaries arranged in a tree
structure, i.e. dictionaries containing other dictionaries as values, and so on...

The intended use of this module is to import the module and access all functions through the module
object, like so:
    from utils import treedict
    from pprint import pprint

    d = {}
    treedict.set(d, 1, 2, 3)
    treedict.set(d, 1, 5, 4, 6)
    pprint(d)
"""


def new(iterable):
    D = dict()
    update(D, iterable)
    return D


def update(D, iterable):
    for path in iterable:
        set(D, *path)


def get(D, *path):
    for elem in path:
        D = D[elem]
    return D


def getdefault(D, *path_plus_default):
    """Get a path from the tree dictionary. If the given path does not exist in the treedict, the
    default value is returned."""
    default = path_plus_default[-1]
    path = path_plus_default[:-1]
    try:
        for elem in path:
            D = D[elem]
    except KeyError:
        return default
    else:
        return D


def has(D, *path):
    try:
        get(D, *path)
        return True
    except KeyError:
        return False


def set(D, *path):
    # go down path as long as possible
    cls = type(D)
    iterator = iter(path[:-2])
    for elem in iterator:
        try:
            next_D = D[elem]
        except KeyError:
            next_D = D[elem] = cls()
            D = next_D
            # build missing part of path (and keep going down)
            for elem in iterator:
                next_D = D[elem] = cls()
                D = next_D
            break
        D = next_D
    # and finally make the assignment
    D[path[-2]] = path[-1]
    return path[-1]


def setdefault(D, *path_plus_default):
    """Like dict.setdefault(), returns treedict.get(D, *path). If the path does not exist, it is
    created and the default value is set."""
    path = path_plus_default[:-1]
    try:
        return get(D, *path)
    except KeyError:
        return set(D, *path_plus_default)


def pop(D, *path):
    D = get(D, *path[:-1])
    return D.pop(path[-1])


def pop_path(D, *path):
    """Same as treedict.pop(), but deletes the dictionaries in the path if they become empty
    after the removal of the item."""
    dicts = []
    for elem in path[:-1]:
        dicts.append(D)
        D = D[elem]
    value = D.pop(path[-1])
    for elem in reversed(path[:-1]):
        D = dicts.pop()
        if len(D[elem]) == 0:
            del D[elem]
        else:
            break
    return value

# setup some aliases for pop() and pop_path()
remove = pop
remove_path = pop_path


def iteritems(D, depth=None):
    stack = [D.iteritems()]
    path = []
    while len(stack) > 0:
        iterator = stack[-1]
        for key, value in iterator:
            path.append(key)
            if isinstance(value, dict) and (depth is None or len(path) < depth):
                stack.append(value.iteritems())
                break
            path.append(value)
            yield tuple(path)
            path.pop()
            path.pop()
        # pop stack if the for loop above has run till the end
        if iterator is stack[-1]:
            stack.pop()
            if len(path) > 0:
                path.pop()


def copy(D, depth=None):
    clone = type(D)()
    update(clone, iteritems(D, depth))
    return clone

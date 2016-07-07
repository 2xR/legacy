from itertools import izip


def common_prefix(*sequences):
    """Return the longest common prefix among the argument sequences."""
    prefix = []
    for values in izip(*sequences):
        values = iter(values)
        first = values.next()
        if any(value != first for value in values):
            break
        prefix.append(first)
    return prefix


def common_suffix(*sequences):
    """Return the longest common suffix among the argument sequences."""
    reversed_sequences = (reversed(s) for s in sequences)
    suffix = []
    for values in izip(*reversed_sequences):
        values = iter(values)
        first = values.next()
        if any(value != first for value in values):
            break
        suffix.append(first)
    suffix.reverse()
    return suffix


def common_mro(*classes):
    """Find the common part of the MROs (method resolution order) of the argument classes."""
    return common_suffix(*(cls.mro() for cls in classes))


def common_type(*values):
    """Find the most specialized common type among the argument values."""
    classes = {type(value) for value in values}
    if len(classes) == 1:
        return iter(classes).next()
    return common_suffix(*(cls.mro() for cls in classes))[0]

"""Perform basic operations on multiple dictionaries, like key lookups and and merging."""
from utils.misc import UNDEF


def lookup(dicts, key, default=UNDEF):
    """Look up a key in a sequence of dictionaries. If the key isn't found in any of the provided
    dictionaries, return 'default' if provided, otherwise raise KeyError."""
    for d in dicts:
        try:
            return d[key]
        except KeyError:
            pass
    if default is not UNDEF:
        return default
    raise KeyError("unable to find key %r in multidict lookup" % (key,))


def has_key(dicts, key):
    """Return True if 'key' can be found in any of the given dictionaries, False otherwise."""
    try:
        lookup(dicts, key)
        return True
    except KeyError:
        return False


def merge(dicts):
    """Create a new dictionary containing the pairs in all the given dictionaries. The keys are
    introduced in order, meaning that if a key appears in multiple dictionaries, the value
    appearing later in the sequence will overwrite any previous value."""
    m = {}
    for d in dicts:
        m.update(d)
    return m


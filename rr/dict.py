def diff(a, b):
    """Compute the *asymmetric* difference between dictionaries a and b. The resulting dictionary
    includes keys from a which are not present in b, plus all keys in a whose value is different
    in b. All values are obtained from dictionary a."""
    return {k: v for (k, v) in a.iteritems() if k not in b or v != b[k]}


def extract(d, keys, skip_missing_keys=False):
    """Create a dictionary by only extracting the keys in 'keys' from 'd'. Raises a KeyError if a
    key is not present in 'd' and 'skip_missing_keys' is false, otherwise silently skips the key.
    """
    if skip_missing_keys:
        return {k: d[k] for k in keys if k in d}
    else:
        return {k: d[k] for k in keys}


def lookup(d, *keys):
    """Lookup all argument 'keys' in 'd', in order. Returns the value associated with the first
    key that is found in 'd'. If none of the keys are found, KeyError is raised."""
    for k in keys:
        try:
            return d[k]
        except KeyError:
            pass
    raise KeyError(repr(keys))

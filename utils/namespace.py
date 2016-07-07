from utils.copy import fetch_copy
from copy import deepcopy


class Namespace(dict):
    """Utility class that works as a dict or as a regular object. Users can add string keys
    through attribute assignment, and/or regular subscripting. The following are equivalent:
        ns.x = 3
        ns["x"] = 3
    For non-string keys subscripting is required, as the attribute-like notation only allows
    string keys with the usual character limitations (no #$!? etc. allowed)."""
    __slots__ = ()
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    @property
    def __dict__(self):
        """Emulate a normal object with a __dict__ attribute."""
        return self

    def __deepcopy__(self, memo):
        clone = fetch_copy(self, memo)
        for key, value in dict.iteritems(self):
            clone[deepcopy(key, memo)] = deepcopy(value, memo)
        return clone

    # --------------------------------------------------------------------------
    # Pickle protocol
    def __getstate__(self):
        return dict(self)

    def __setstate__(self, d):
        self.update(d)

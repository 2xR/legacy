from __future__ import absolute_import
from contextlib import contextmanager


@contextmanager
def ignoring(*exceptions):
    """This context manager simply ignores any of the given exceptions occurring within its
    scope. Note however that any exception that reaches this context manager will make the block
    end prematurely, and that should be taken into account if this behavior is not desired."""
    try:
        yield
    except exceptions:
        pass

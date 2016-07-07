"""This module contains utility functions to work with directories."""
import sys
from contextlib import contextmanager
from os.path import abspath, join, dirname, pardir


def up(path, levels=1):
    return abspath(join(dirname(path), *([pardir] * levels)))


def augment_sys_path(*dirs):
    """Augment the list of directories where python looks for modules."""
    sys.path.extend(dirs)


@contextmanager
def augmented_sys_path(*dirs):
    """Temporarily augment the list of directories where python looks for modules."""
    augment_sys_path(dirs)
    yield
    map(sys.path.remove, dirs)

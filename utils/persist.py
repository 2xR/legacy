import cPickle
import dumbdbm
import shelve
import os


# ------------------------------------------------------------------------------
# main functions of this module: save() and load()
def save(data, *args, **kwargs):
    """Generic persistence function. This function uses a method protocol composed of three
    steps, all of which can be optionally defined by 'data'. The methods are __presave__(),
    __save__(), and __postsave__(), which are called before, during, and after saving. If no
    __save__() method is defined, save_to_pickle() is used as a default. The first method in
    the save protocol (__presave__()) can return modified versions of args and kwargs, which
    are passed to the subsequent methods in the protocol. This way, one can, for instance,
    append a file extension to a filename before passing the arguments to __save__().
    If None is returned by __presave__() positional and keyword arguments are unmodified.
    The return value of __save__() is ignored, and finally, if __postsave__() exists, it is
    called and its return value becomes the return value of this function."""
    # call __presave__() (bound to data)
    cls = type(data)
    pre_save = getattr(cls, "__presave__", None)
    if callable(pre_save):
        modified_args = pre_save(data, *args, **kwargs)
        if modified_args is not None:
            args, kwargs = modified_args
    # call __save__() (bound to data)
    save = getattr(cls, "__save__", save_to_pickle)
    save(data, *args, **kwargs)
    # call __postsave__() (bound to data)
    post_save = getattr(cls, "__postsave__", None)
    if callable(post_save):
        return post_save(data, *args, **kwargs)
    return None


def load(cls, *args, **kwargs):
    """The complement of save(), this is a generic function to load objects from storage using a
    method protocol similar to save(). The argument class can provide methods __preload__(),
    __load__() (load_from_pickle() is used if 'cls' doesn't define it), and __postload__(). Like
    __presave__(), __preload__() can modify the arguments passed to the other two methods. The
    __load__() method must return the object being loaded, which is given as the first argument to
    __postload__(). The return value of __postload__() is ignored. This function returns the object
    returned by __load__()."""
    # call __preload__() (unbound or bound to cls)
    pre_load = getattr(cls, "__preload__", None)
    if callable(pre_load):
        modified_args = pre_load(*args, **kwargs)
        if modified_args is not None:
            args, kwargs = modified_args
    # call __load__() (unbound or bound to cls)
    load = getattr(cls, "__load__", load_from_pickle)
    data = load(*args, **kwargs)
    # call __postload__() (bound to data)
    post_load = getattr(cls, "__postload__", None)
    if callable(post_load):
        post_load(data, *args, **kwargs)
    return data


# ------------------------------------------------------------------------------
# basic functions that can be used as __load__() and __save__()
def load_from_pickle(filepath, protocol=2, pickle=cPickle):
    if not os.path.isfile(filepath):
        raise ValueError("provided path is not a file")
    mode = "r" + ("b" if protocol != 0 else "")
    with open(filepath, mode) as istream:
        return pickle.load(istream)


def save_to_pickle(data, filepath, protocol=2, pickle=cPickle):
    mode = "w" + ("b" if protocol != 0 else "")
    with open(filepath, mode) as ostream:
        pickle.dump(data, ostream, protocol)


def load_from_shelve(filepath, key="data", use_dumbdbm=True):
    if not os.path.isfile(filepath):
        raise ValueError("provided path is not a file")
    if use_dumbdbm:
        filepath = filepath.rsplit(".", 1)[0]
    db = shelve.Shelf(dumbdbm.open(filepath)) if use_dumbdbm else shelve.open(filepath)
    data = db[key]
    db.close()
    return data


def save_to_shelve(data, filepath, key="data", use_dumbdbm=True):
    db = shelve.Shelf(dumbdbm.open(filepath)) if use_dumbdbm else shelve.open(filepath)
    db[key] = data
    db.close()


# ------------------------------------------------------------------------------
# creation of classes with persistence interface
def attach_persistence_interface(cls):
    """Add save() and load() to 'cls' to be used as methods of its instances."""
    setattr(cls, save.__name__, save)
    setattr(cls, load.__name__, classmethod(load))


class Persistent(object):
    __slots__ = ()
    save = save
    load = classmethod(load)


class ShelvePersistent(Persistent):
    __slots__ = ()
    __save__ = save_to_shelve
    __load__ = classmethod(load_from_shelve)


# ------------------------------------------------------------------------------
# small example
def example():
    class foo(object):
        extension = ".bar"

        def __presave__(self, filepath):
            print "preparing save to", filepath
            if not filepath.endswith(foo.extension):
                print "adding file extension to", filepath
                filepath += foo.extension
            return (filepath,), {}

        def __save__(self, filepath):
            print "saving to", filepath

        def __postsave__(self, filepath):
            print "saved to", filepath
            return self

        @classmethod
        def __preload__(cls, filepath):
            print "preparing load from", filepath
            if not filepath.endswith(foo.extension):
                print "adding file extension to", filepath
                filepath += foo.extension
            return (filepath,), {}

        @classmethod
        def __load__(cls, filepath):
            print "loading from", filepath
            return cls()

        def __postload__(self, filepath):
            print "loaded from", filepath

    f = foo()
    save(f, "omg")
    g = load(foo, "awesome")
    return f, g

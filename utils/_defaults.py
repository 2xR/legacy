from IPython.core.magic_arguments import defaults
from utils.chaindict import chaindict


def build(obj, params, undefined=None, config_attr="defaults"):
    config = chaindict()
    for cls in type(obj).mro():
        if config_attr in cls.__dict__:
            config.parents.append(cls.__dict__[config_attr])
    update(config, params, undefined)
    return config


def update(config, params, undefined=None):
    for param, value in params.iteritems():
        if value != undefined:
            config[param] = value


def apply(obj, config, setparam=setattr):
    for param, value in config.iteritems():
        setparam(obj, param, value)


def set(obj, params, undefined=None, setparam=setattr):
    config = build(obj, params, undefined)
    apply(obj, config, setparam)



class Config(chaindict):
    """Hierarchical configuration object. Attribute lookups search the tree from specific to
    general configuration values, e.g. a config.hud.font will first look in 'config.hud' for a
    key 'font', and if that fails, it looks in config for the application-wide font parameter
    'config.font'."""
    def __init__(self, *parents):
        self.__parents = list(parents)

    @classmethod
    def unbound(cls, **kwargs):


    def __getattr__(self, name):
        parent = self.__parents
        if parent is None:
            raise AttributeError("unable to find %r in config" % name)
        try:
            return getattr(parent, name)
        except AttributeError:
            raise AttributeError("unable to find %r in config" % name)

    __setitem__ = object.__setattr__
    __getitem__ = object.__getattribute__

    @property
    def is_root(self):
        return self.__parents is None

    @property
    def depth(self):
        d = -1
        cfg = self
        while cfg is not None:
            d += 1
            cfg = cfg.__parents
        return d

    def read_file(self, filepath):
        execfile(filepath, globals(), self)

    @classmethod
    def from_file(cls, filepath):
        config = cls()
        config.read_file(filepath)
        return config


config = Config()
config.font = Config(config, name="arial", size=14)
config.app = Config()


class foo(object):
    class defaults(config):
        param1 = False
        verbose = True

class bar(foo):
    class defaults(foo.defaults):
        param1 = 2


class foo(object):
    defaults = config(param1=False,
                      verbose=True)

class bar(foo):
    defaults config(foo.config)



from utils.misc import UNDEF


VALUE_ATTR = "value"


class Config(object):
    VALUE_ATTR = VALUE_ATTR

    def __init__(self, **kwargs):
        self.__dict__[VALUE_ATTR] = kwargs.pop(VALUE_ATTR, UNDEF)
        if len(kwargs) > 0:
            for k, v in kwargs.iteritems():
                self[k] = v

    def __getattr__(self, k):
        D = self.__dict__
        try:
            return D[k]
        except KeyError:
            return UndefinedConfig(self, k)

    __getitem__ = __getattr__

    def __setattr__(self, k, v):
        if k == VALUE_ATTR:
            self.__dict__[k] = v
        else:
            self.__dict__[k] = child = type(self)()
            child[VALUE_ATTR] = v



class UndefinedConfig(object):
    def __init__(self, config, *path):
        self.__dict__.update(__config__=config, __path__=path)

    def __getattr__(self, k):
        D = self.__dict__
        return type(self)(D["__config__"], D["__path__"] + (k,))

    def __setattr__(self, k, v):
        D = self.__dict__
        config = D["__config__"]
        for key in D["__path__"]:
            if key in config.__dict__:


        D["__config__"].
        self.config


"""
cfg = Config(foo=3,
             bar=4)
cfg.baz = Config(foo=2,
                 bar=1)
cfg.baz.foo -> Config(value=UNDEF)
"""

"""
font_size = "14sp"
font_face = "arial"

score_label = Config()
score_label.font_size = "20sp"
score_label.font_face = "times"


"""


class Config(object):
    """A hierarchical configuration tree. Attribute lookups search the tree from specific to
    general configuration values, e.g. a config.hud.font will first look in 'config.hud' for a
    key 'font', and if that fails, it looks in config for the application-wide font parameter
    'config.font'."""
    def __init__(self, parent=None, editable=False):
        self.__parent = parent
        self.__editable = editable

    def __getattr__(self, name):
        try:
            return self.lookup(name)
        except AttributeError, error:
            if self.editable:
                new_config = type(self)(parent=self)
                setattr(self, name, new_config)
                return new_config
            else:
                raise error

    def lookup(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            if self.editable:
                raise AttributeError("unable to find %r in editable config" % name)
            else:
                parent = self.__dict__["parent"]
                if parent is None:
                    raise AttributeError("unable to find %r in non-editable config" % name)
                return parent.lookup(name)

    @property
    def editable(self):
        dic = self
        while dic is not None:
            if dic.__dict__["__editable"]:
                return True
            dic = dic.__dict__["__parent"]
        return False

    @editable.setter
    def editable(self, value):
        self.__dict__["__editable"] = bool(value)

    @contextmanager
    def edit_mode(self):
        editable = self.__dict__["__editable"]
        self.editable = True
        yield
        self.editable = editable

    @property
    def is_root(self):
        return self.__dict__["__parent"] is None

    @property
    def depth(self):
        d = -1
        dic = self
        while dic is not None:
            d += 1
            dic = dic.__dict__["__parent"]
        return d

    def read_file(self, filepath):
        with self.edit_mode():
            execfile(filepath, globals(), self)

    @classmethod
    def from_file(cls, filepath):
        config = cls()
        config.read_file(filepath)
        return config


##class Config(object):
##    """A hierarchical configuration tree. Attribute lookups search the tree from specific to
##    general configuration values, e.g. a config.hud.font will first look in 'config.hud' for a
##    key 'font', and if that fails, it looks in config for the application-wide font parameter
##    'config.font'."""
##    def __init__(self, parent=None, editable=False):
##        self.__dict__["__parent"] = parent
##        self.__dict__["__editable"] = editable
##
##    def __repr__(self):
##        return self.str()
##
##    def str(self, indentation=1):
##        indent = " ." * indentation
##        parts = []
##        for name, value in self.__dict__.iteritems():
##            if name not in ("__parent", "__editable"):
##                if isinstance(value, Config):
##                    parts.extend([indent, "<", name, "\n",
##                                  value.str(indentation + 1),
##                                  indent, ">\n"])
##                else:
##                    parts.append("%s%s = %s\n" % (indent, name, value))
##        if self.__dict__["__editable"]:
##            parts.insert(0, indent + "# EDITABLE #\n")
##            parts.append(indent + "# EDITABLE #\n")
##        return "".join(parts)
##
##    def __getattr__(self, name):
##        try:
##            return self.lookup(name)
##        except AttributeError, error:
##            if self.editable:
##                new_config = Config(parent=self)
##                setattr(self, name, new_config)
##                return new_config
##            else:
##                raise error
##
##    def lookup(self, name):
##        try:
##            return self.__dict__[name]
##        except KeyError:
##            if self.editable:
##                raise AttributeError("unable to find %r in editable config" % name)
##            else:
##                parent = self.__dict__["parent"]
##                if parent is None:
##                    raise AttributeError("unable to find %r in non-editable config" % name)
##                return parent.lookup(name)
##
##    @property
##    def editable(self):
##        dic = self
##        while dic is not None:
##            if dic.__dict__["__editable"]:
##                return True
##            dic = dic.__dict__["__parent"]
##        return False
##
##    @editable.setter
##    def editable(self, value):
##        self.__dict__["__editable"] = bool(value)
##
##    @contextmanager
##    def edit_mode(self):
##        editable = self.__dict__["__editable"]
##        self.editable = True
##        yield
##        self.editable = editable
##
##    @property
##    def is_root(self):
##        return self.__dict__["__parent"] is None
##
##    @property
##    def depth(self):
##        d = -1
##        dic = self
##        while dic is not None:
##            d += 1
##            dic = dic.__dict__["__parent"]
##        return d
##
##    def readfile(self, filepath):
##        with self.edit_mode():
##            execfile(filepath, globals(), self)
##
##
##config = Config()
##config.readfile(os.path.join(os.path.dirname(__file__), "..", "resources", "config.py"))

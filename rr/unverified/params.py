from sys import stdout

from utils import container
from utils.misc import UNDEF
from utils.namespace import Namespace
from utils.prettyrepr import prettify_class


@prettify_class
class Param(object):
    __slots__ = ("name", "description", "options", "domain",
                 "default", "fget", "fset", "fadapt")

    def __init__(self, name=None, description="<description unavailable>",
                 options=None, domain=None, default=UNDEF,
                 fget=None, fset=None, fadapt=None):
        self.name = name
        self.description = description
        self.options = options
        self.domain = None if domain is None else container.new(domain)
        self.default = default
        self.fget = fget
        self.fset = fset
        self.fadapt = fadapt

    def __info__(self):
        return repr(self.name)

    def copy(self, **overrides):
        clone = type(self)(name=self.name,
                           description=self.description,
                           options=self.options,
                           domain=self.domain,
                           default=self.default,
                           fget=self.fget,
                           fset=self.fset,
                           fadapt=self.fadapt)
        if len(overrides) > 0:
            for attr, value in overrides.iteritems():
                setattr(clone, attr, value)
        return clone

    # --------------------------------------------------------------------------
    # property()-like interface
    def getter(self, fnc):
        return self.copy(fget=fnc)

    def setter(self, fnc):
        return self.copy(fset=fnc)

    def adapter(self, fnc):
        return self.copy(fadapt=fnc)

    __call__ = getter

    # --------------------------------------------------------------------------
    # Object manipulation
    def init(self, paramset):
        self.set(paramset, paramset.Defaults.get(self.name, self.default))

    reset = clear = init

    def validate(self, paramset):
        """Returns True if the parameter's value is in the domain or no domain was specified."""
        return self.domain is None or self.get(paramset) in self.domain

    def get(self, paramset):
        if self.fget is not None:
            return self.fget(paramset)
        return paramset.value_of[self]

    def set(self, paramset, value):
        """Set a new value for this parameter. This calls (if available) the adapter function,
        validates the new value against the domain, and only then calls the _set() method to
        actually set the new value."""
        if self.fadapt is not None:
            value = self.fadapt(paramset, value)
        if self.domain is not None and value not in self.domain:
            raise ValueError("{!r}: value outside domain ({!r} not in {!r})"
                             .format(self.name, value, self.domain))
        self._set(paramset, value)

    def _set(self, paramset, value):
        """This private method is where the parameter value is actually changed. This is called
        only after adapting and validating the value passed to the set() method."""
        if self.fset is not None:
            self.fset(paramset, value)
        paramset.value_of[self] = value

    # --------------------------------------------------------------------------
    # Report and help messages
    def report(self, paramset, ostream=stdout):
        ostream.write("{!r}: {!r}\n".format(self.name, self.get(paramset)))

    def help(self, paramset, ostream=stdout):
        ostream.write("{}: {}\n".format(self.name, self.description))
        if self.options is not None:
            ostream.write("\toptions = {}\n".format(self.options))
        elif self.domain is not None:
            ostream.write("\tdomain = {!r}\n".format(self.domain))
        default = paramset.Defaults.get(self.name, self.default)
        if default is not UNDEF:
            ostream.write("\tdefault = {!r}\n".format(default))

    # --------------------------------------------------------------------------
    # Descriptor protocol
    def __get__(self, paramset, cls):
        return self if paramset is None else self.get(paramset)

    __set__ = set
    __delete__ = reset


class ParamSetMeta(type):
    def __init__(cls, name, bases, dict):
        super(ParamSetMeta, cls).__init__(name, bases, dict)

        # compute the parameter set of 'cls' from the parameter sets of its bases
        params = set()
        for base in bases:
            try:
                base_params = base.__dict__["__params__"]
            except KeyError:
                continue
            else:
                params.update(base_params)

        # and of course also include the parameters defined in 'cls' itself
        for k, v in dict.iteritems():
            if isinstance(v, Param):
                params.add(v)
                # fill in the parameter's name if it's None
                if v.name is None:
                    v.name = k

        # finally we store the set of parameters in the paramset 'cls'
        cls.__params__ = params


class ParamSetDefaults(object):
    @classmethod
    def get(cls, name=None, default=UNDEF):
        if name is None:
            # if no parameter name was provided, we build a dictionary of parameter
            # names and respective default values, in order of class inheritance.
            mapping = {}
            for base in reversed(cls.mro()):
                for attr, value in base.__dict__.iteritems():
                    if not attr.startswith("_"):
                        mapping[attr] = value
            del mapping["get"]
            return mapping
        else:
            # otherwise we simply get the value associated with the given parameter
            # name, or return the 'default' if no such attribute exists.
            return getattr(cls, name, default)


@prettify_class
class ParamSet(object):
    __metaclass__ = ParamSetMeta
    __slots__ = ("owner",     # paramset owner object
                 "value_of")  # {Param: value}
    __params__ = ()
    Defaults = ParamSetDefaults

    def __init__(self, owner, **kwargs):
        self.owner = owner
        self.value_of = {}
        self.init()
        if len(kwargs) > 0:
            self.set(**kwargs)

    def __info__(self):
        return {name: getattr(self, name) for name in self.keys()}

    @classmethod
    def default(cls, name):
        try:
            return getattr(cls.Defaults, name)
        except AttributeError:
            param = getattr(cls, name)
            return param.default

    # --------------------------------------------------------------------------
    # Dictionary-like interface
    @classmethod
    def keys(cls):
        """Returns a set of names of parameters **reachable through normal attribute access**."""
        return {param.name for param in cls.__params__}

    @classmethod
    def iterkeys(cls):
        return iter(cls.keys())

    @classmethod
    def params(cls):
        return list(cls.iterparams())

    @classmethod
    def iterparams(cls):
        """Similar to keys(), but instead of returning parameter names, this iterates through the
        actual Parameter objects that are reachable by this paramset through "normal" means."""
        return (getattr(cls, name) for name in cls.keys())

    def values(self):
        return list(self.itervalues())

    def itervalues(self):
        return (getattr(self, name) for name in self.keys())

    def items(self):
        return list(self.iteritems())

    def iteritems(self):
        return ((name, getattr(self, name)) for name in self.keys())

    __iter__ = iterkeys

    def __getitem__(self, k):
        return getattr(self, k)

    def __setitem__(self, k, v):
        setattr(self, k, v)

    def __delitem__(self, k):
        delattr(self, k)

    def __len__(self):
        return len(self.value_of)

    def __contains__(self, param):
        if isinstance(param, str):
            return hasattr(self, param)
        elif isinstance(param, Param):
            return param is getattr(type(self), param.name)
        else:
            return False

    # --------------------------------------------------------------------------
    # Param-like interface
    def init(self):
        for param in self.iterparams():
            param.init(self)

    def validate(self):
        undefined = []
        invalid = []
        for param in self.iterparams():
            if param.get(self) is UNDEF:
                undefined.append(param.name)
            elif not param.validate(self):
                invalid.append(param.name)
        error_msgs = []
        if len(undefined) > 0:
            error_msgs.append("{} undefined parameters: {}".format(len(undefined), undefined))
        if len(invalid) > 0:
            error_msgs.append("{} parameters with invalid values: {}".format(len(invalid), invalid))
        if len(error_msgs) > 0:
            raise ValueError("\n".join(error_msgs))
        return True

    def get(self):
        """Returns a namespace with the current values of all parameters. Can be useful for taking
        quick snapshots of an object's current configuration and later restore it using the set()
        method."""
        return Namespace(self.iteritems())

    def set(self, *args, **kwargs):
        """Sets the current values of one or more parameters. This method's arguments have the
        same meaning as in dict.update(), i.e. positional arguments should be dictionaries or
        iterables of (name, value) pairs, and keyword arguments can also be supplied at the end.
        """
        if len(args) > 0:
            for arg in args:
                if isinstance(arg, dict):
                    arg = arg.iteritems()
                for name, value in arg:
                    setattr(self, name, value)
        if len(kwargs) > 0:
            for name, value in kwargs.iteritems():
                setattr(self, name, value)

    update = set

    def reset(self):
        """Sets all parameters back to their defaults."""
        for param in self.iterparams():
            param.reset(self)

    clear = reset

    # --------------------------------------------------------------------------
    # Report and help messages
    def report(self, ostream=stdout):
        cls = type(self)
        for name in sorted(cls.iterkeys()):
            param = getattr(cls, name)
            param.report(self, ostream)

    def help(self, param=None, ostream=stdout):
        if param is not None:
            param_obj = getattr(type(self), param, None)
            if isinstance(param_obj, Param):
                param_obj.help(self, ostream)
            else:
                ostream.write("Unknown parameter: {!r}".format(param))
            return

        ostream.write("*** Parameter set for {!r} ***\n".format(self.owner))
        if len(self.__params__) == 0:
            ostream.write("\nEmpty parameter set.\n")
        else:
            cls = type(self)
            for name in sorted(self.iterkeys()):
                ostream.write("\n")
                param = getattr(cls, name)
                param.help(self, ostream)


Param.Set = ParamSet


def example():
    class FooParams(Param.Set):
        bar = Param(description="to bar or not to bar", domain=(False, True), default=False)

        @bar.setter
        def bar(self, b):
            print("bar: {} -> {}".format(self.values.get(type(self).bar, UNDEF), b))

        @bar.adapter
        def bar(self, b):
            if not isinstance(b, bool):
                print("adapting {!r} to boolean -> {}".format(b, bool(b)))
            return bool(b)

    class Foo(object):
        def __init__(self):
            self.params = FooParams(self)

    foo = Foo()
    foo.params.bar = True
    del foo.params.bar
    foo.params.bar = 1
    foo.params.bar = 0
    return foo

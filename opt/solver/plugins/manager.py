from utils.prettyrepr import prettify_class
from utils.namespace import Namespace
from utils.misc import check_type

from .plugin import Plugin


@prettify_class
class PluginManager(object):
    """
    This object manages the plugins attached to a solver.  Each plugin has an associated name so
    that it can be accessed through the manager's namespace.
    """
    def __init__(self, solver):
        self.solver = solver
        self.namespace = Namespace()

    def __info__(self):
        return self.namespace

    def __iter__(self):
        return self.namespace.itervalues()

    def __len__(self):
        return len(self.namespace)

    def __contains__(self, plugin):
        if isinstance(plugin, basestring):
            return plugin in self.namespace
        elif isinstance(plugin, Plugin):
            return plugin is self.namespace.get(plugin.name, None)
        elif issubclass(plugin, Plugin):
            return any(type(p) is plugin for p in self.namespace.itervalues())
        else:
            return NotImplemented

    def __getitem__(self, name):
        return self.namespace[name]

    def __delitem__(self, name):
        self.remove(self.namespace[name])

    def add(self, plugin):
        """Add a plugin to the plugin manager. The argument can be a plugin object or a callable
        taking no arguments that returns a plugin object."""
        if not isinstance(plugin, Plugin) and callable(plugin):
            plugin = plugin()
        check_type(plugin, Plugin)
        if plugin.name in self.namespace:
            raise NameError("duplicate plugin name {!r}".format(plugin.name))
        self.namespace[plugin.name] = plugin
        plugin.install(self.solver)

    def extend(self, plugins):
        """Add multiple plugins to the manager in one go."""
        for plugin in plugins:
            self.add(plugin)

    update = extend

    def remove(self, plugin):
        check_type(plugin, Plugin)
        if self.namespace[plugin.name] is not plugin:
            raise ValueError("argument does not match plugin registered with the same name")
        del self.namespace[plugin.name]
        plugin.uninstall()

    def discard(self, plugin):
        if plugin in self:
            self.remove(plugin)

    def clear(self):
        for plugin in self.namespace.itervalues():
            plugin.uninstall()
        self.namespace.clear()

    reset = clear

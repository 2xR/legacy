from utils.prettyrepr import prettify_class


@prettify_class
class Plugin(object):
    """
    Base class for solver plugins. Plugin classes (or individual instances) should define a
    mapping 'signal_map' of signal types to the name of the target method to be called when the
    signal is emitted on the solver's channel. Note that listener callbacks should take the
    listener as single argument.  It is also possible to define callbacks which do not take the
    listener as argument (e.g. payload, signal, or no argument) by using '(target, callback_mode)'
    tuples as values in the signal map.

    Plugins may also emit new signals, which are automatically registered in the solver's channel
    if they're present in the plugin's 'emits' attribute.  This can be a class attribute containing
    an iterable of signal types that will be registered/unregistered automatically when the plugin
    is installed/uninstalled, respectively.

    This base class defines only two methods, install() and uninstall(), in which the listeners
    are added to/removed from the solver's channel, respectively.
    """
    signal_map = {}
    listener_priority = 0.0
    emits = ()

    def __init__(self, name=None):
        if name is None:
            name = type(self).__name__
        self.name = name
        self.solver = None
        self.listeners = []
        self.installed = False

    def install(self, solver):
        if not self.installed:
            self.solver = solver
            if len(self.emits) > 0:
                solver.channel.register(*self.emits)
            for signal, target in self.signal_map.iteritems():
                if isinstance(target, (tuple, list)) and len(target) == 2:
                    callback = getattr(self, target[0])
                    callback_mode = target[1]
                else:
                    callback = getattr(self, target)
                    callback_mode = None
                listener = solver.channel.listen(signal, callback=callback,
                                                 callback_mode=callback_mode,
                                                 priority=self.listener_priority)
                self.listeners.append(listener)
            self.installed = True
            return True
        elif solver is not self.solver:
            raise Exception("attempting to install plugin to multiple solvers")
        return False

    def uninstall(self):
        if self.installed:
            if len(self.emits) > 0:
                self.solver.channel.unregister(*self.emits)
            for listener in self.listeners:
                listener.stop()
            self.solver = None
            self.listeners = []
            self.installed = False
            return True
        return False

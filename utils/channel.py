from bisect import insort_right, bisect_left
from sys import stdout

from utils.misc import callable_name, check_type
from utils.prettyrepr import prettify_class
from utils.multiset import MultiSet
from utils.relations import One, Many


LOG_FMT = "[{:>10} @ {:<20}] {:2}) {}{}\n"


def make_log_fnc(ostream=stdout):
    """Log function factory. The returned log function writes its output into the argument stream
    (a file-like object, default is sys.stdout). The returned function is appropriate to be used
    as a log function for the channel object."""
    def log_fnc(channel, obj):
        n = len(channel.stack)
        ind = "  " * (n - 1)
        owner = "" if obj.owner is None else obj.owner
        ostream.write(LOG_FMT.format(owner, channel._fullname, n, ind, obj))
    return log_fnc


# callback modes used in listener activation
CALLBACK_NO_ARGS = 0
CALLBACK_TAKES_LISTENER = 1
CALLBACK_TAKES_SIGNAL = 2
CALLBACK_TAKES_PAYLOAD = 3
CALLBACK_MODES = (CALLBACK_NO_ARGS,
                  CALLBACK_TAKES_LISTENER,
                  CALLBACK_TAKES_SIGNAL,
                  CALLBACK_TAKES_PAYLOAD)


@prettify_class
class Channel(object):
    """This class implements a channel for asynchronous communication using Signal and Listener
    primitives. Users are not required to use the primitive classes directly. Instead, the listen()
    and emit() methods should be used.

    component_A.py

        def bar(listener):
            signal = listener.match
            print signal

        channel = Channel()
        channel.listen("foo", callback=bar)  # wait until a matching signal is heard

    ... and later, possibly by another component ignorant of the listener
    component_B.py

        channel.emit("foo")  # A's listener will be activated now and print the signal

    A hierarchy of channels can be set up by linking channels through their 'parent'/'children'
    attributes. Whenever a signal is emitted in a channel, after activating the local listeners,
    the channel emits the same signal on the parent channel (if a parent is available).
    """
    __slots__ = ("_name",             # channel name (for pretty logging)
                 "_fullname",         # channel full name (for pretty logging)
                 "_parent",           # parent channel
                 "_children",         # dictionary of child channels
                 "type_validation",   # True if validating signal and listener types
                 "registered_types",  # multiset of accepted signal/listener types
                 "listeners",         # {signal_type: [Listener]}
                 "callback_mode",     # default listener callback mode
                 "log_fnc",           # log function
                 "stack")             # active signals and listeners (for pretty logging)

    make_log_fnc = staticmethod(make_log_fnc)
    NAME_SEPARATOR = "."

    CALLBACK_NO_ARGS = CALLBACK_NO_ARGS
    CALLBACK_TAKES_LISTENER = CALLBACK_TAKES_LISTENER
    CALLBACK_TAKES_SIGNAL = CALLBACK_TAKES_SIGNAL
    CALLBACK_TAKES_PAYLOAD = CALLBACK_TAKES_PAYLOAD
    CALLBACK_MODES = CALLBACK_MODES

    def __init__(self, name, parent=None, type_validation=True, register_types=None,
                 callback_mode=CALLBACK_TAKES_LISTENER, log_fnc=None):
        check_type(name, basestring)
        sep = type(self).NAME_SEPARATOR
        if sep in name:
            raise NameError("name cannot contain {!r}".format(sep))
        self._name = name
        self._fullname = name
        self._parent = None
        self._children = {}
        self.type_validation = type_validation
        self.registered_types = MultiSet()
        self.listeners = {}
        self.callback_mode = callback_mode
        self.log_fnc = log_fnc
        self.stack = []
        if parent is not None:
            self.parent = parent
        if register_types is not None:
            self._register_propagate(register_types)

    def __info__(self):
        if self.type_validation:
            signal_types = set(self.registered_types)
        else:
            signal_types = set(self.listeners.iterkeys())
        signal_types.add(None)
        listener_data = []
        for signal_type in sorted(signal_types):
            try:
                signal_listeners = self.listeners[signal_type]
            except KeyError:
                signal_listeners = ()
            listener_data.append("{!r} ({})".format(signal_type, len(signal_listeners)))
        return ("{}, type_validation={}, {{{}}}"
                .format(self._fullname,
                        self.type_validation,
                        ", ".join(listener_data)))

    def log_to(self, ostream):
        """Set a log function for the channel.  If 'ostream' is None, the log function is
        disabled, otherwise 'make_log_fnc()' is used to create a log function targeting the
        argument file-like object."""
        if ostream is None:
            self.log_fnc = None
        else:
            self.log_fnc = make_log_fnc(ostream)

    def forward_to(self, channel):
        """This is a shortcut to create a listener that activates on any signal and emits the
        it unchanged on the argument channel."""
        assert channel is not self
        channel._register_propagate(self.registered_types)
        return self.listen(type=Signal.ANY,
                           callback=channel.emit,
                           callback_mode=CALLBACK_TAKES_SIGNAL)

    # --------------------------------------------------------------------------
    # Type (un)registration methods
    def register(self, *types):
        """Register new signal types in the channel. If type validation is enabled, a channel will
        not accept signals or listeners of a given type before it is registered."""
        self._register_propagate(types)

    def _register_propagate(self, types):
        """Internal method. Registers signal types in 'types' (may be an iterable or a mapping)
        in this channel and propagates upward."""
        channel = self
        while channel is not None:
            channel.registered_types.update(types)
            channel = channel._parent

    def unregister(self, *types):
        """Remove (if present) one or more given signal type from the channel."""
        self._unregister_propagate(types)

    def _unregister_propagate(self, types):
        """Internal method. Unregisters signal types in 'types' (may be an iterable or a mapping)
        in this channel and propagates upward."""
        channel = self
        while channel is not None:
            channel.registered_types.difference_update(types)
            channel = channel._parent

    # --------------------------------------------------------------------------
    # "Public" methods
    def listen(self, type, callback, callback_mode=None, condition=None, priority=0.0, owner=None):
        """Creates a Listener object and attaches it to the channel. Returns the new listener.
        Use a type of Channel.Signal.ANY to activate on any signal emitted on the channel."""
        listener = Listener(self, type, callback, callback_mode, condition, priority, owner)
        listener.start()
        return listener

    def emit(self, type, payload=None, owner=None):
        """Creates a Signal object and broadcasts it on the channel. Returns the new signal."""
        if isinstance(type, Signal):
            signal = Signal(self, type.type, type.payload, type.owner)
            if payload is not None:
                signal.payload = payload
            if owner is not None:
                signal.owner = owner
        else:
            signal = Signal(self, type, payload, owner)
        signal.emit()
        return signal

    # --------------------------------------------------------------------------
    # Private methods (used by Signal and Listener objects)
    def _insert(self, listener):
        # error checking
        if listener._channel is not self:
            raise ValueError("listener is not associated with this channel")
        if listener._deployed:
            raise ValueError("duplicate attempt to deploy listener")
        type = listener._type
        if self.type_validation and type != Signal.ANY and type not in self.registered_types:
            raise ValueError("unable to listen signal type {!r} (not registered)".format(type))
        # now we actually insert the listener into our listener table
        try:
            listeners = self.listeners[type]
        except KeyError:
            listeners = self.listeners[type] = []
        insort_right(listeners, (listener._priority, listener))
        listener._deployed = True

    def _remove(self, listener):
        if listener._channel is not self:
            raise ValueError("listener is not associated with this channel")
        if not listener._deployed:
            raise ValueError("listener is not deployed")
        listeners = self.listeners[listener._type]
        if len(listeners) == 1:
            assert listeners[0] == (listener._priority, listener)
            del self.listeners[listener._type]
        else:
            index = bisect_left(listeners, (listener._priority, listener))
            assert listeners[index] == (listener._priority, listener)
            listeners.pop(index)
        listener._deployed = False

    def _broadcast(self, signal, propagating=False):
        """Find and activate all listeners attached to this channel which match 'signal'. If the
        channel is linked to a parent channel, the broadcast is propagated to the parent channel
        afterwards."""
        if self.type_validation and signal.type not in self.registered_types:
            raise ValueError("unable to emit signal type {!r} (not registered)".format(signal.type))
        stack = self.stack
        stack.append(signal)
        log = self.log_fnc
        if not propagating and log is not None:
            log(self, signal)
        for type in (signal.type, Signal.ANY):
            try:
                listeners = self.listeners[type]
            except KeyError:
                continue
            for _, listener in list(listeners):
                if listener._deployed and listener._matches(signal):
                    stack.append(listener)
                    if log is not None:
                        log(self, listener)
                    listener._activate(signal)
                    assert stack[-1] is listener
                    stack.pop()
        parent = self._parent
        if parent is not None:
            parent._broadcast(signal, propagating=True)
        assert stack[-1] is signal
        stack.pop()

    # --------------------------------------------------------------------------
    # parent-child relation management
    @property
    def root(self):
        """The root of the channel tree."""
        channel = self
        while channel._parent is not None:
            channel = channel._parent
        return channel

    @One(complement="children")
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        self._parent = parent
        self._update_fullname()

    @Many(complement="parent")
    def children(self):
        return self._children

    @children.accepts
    def children(self, child):
        check_type(child, Channel)
        if child._name in self._children:
            raise NameError("name {!r} already in use".format(child._name))

    @children.adder
    def children(self, child):
        self._children[child._name] = child
        self._register_propagate(child.registered_types)

    @children.remover
    def children(self, child):
        self._children.pop(child._name)
        self._unregister_propagate(child.registered_types)

    @children.contains
    def children(self, channel):
        if isinstance(channel, basestring):
            return channel in self._children
        if isinstance(channel, Channel):
            return channel is self._children.get(channel._name)
        return False

    @children.iter
    def children(self):
        return self._children.itervalues()

    # --------------------------------------------------------------------------
    # name and full name management
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        check_type(name, basestring)
        sep = type(self).NAME_SEPARATOR
        if sep in name:
            raise NameError("name cannot contain {!r}".format(sep))
        if self._parent is not None:
            self._parent._rename_child(self, name)
        self._name = name
        self._update_fullname()

    @property
    def fullname(self):
        return self._fullname

    def _update_fullname(self):
        if self._parent is None:
            self._fullname = self._name
        else:
            sep = type(self).NAME_SEPARATOR
            self._fullname = "{}{}{}".format(self._parent._fullname, sep, self._name)
        for child in self._children.itervalues():
            child._update_fullname()

    def _rename_child(self, child, name):
        if name in self._children:
            raise NameError("name {!r} already in use".format(name))
        assert self._children[child._name] is child
        del self._children[child._name]
        self._children[name] = child


@prettify_class
class Listener(object):
    """Implements a wait for a signal. Whenever some a signal is broadcast with the same type on
    the same channel, the listener will activate. If the type is None, the listener will be
    activated by the next signal to be broadcast in the channel independently of the its type. In
    addition to filtering signals by type, listeners may also have a 'condition' predicate that is
    able to inspect the contents of matching signals to further narrow down the scope of the
    listener and only activate when the desired signals are emitted.
    Listeners also have a 'priority' attribute that defines the order by which listeners are
    activated when a signal triggers multiple listeners simultaneously (smaller priority activate
    first). Listeners with the same priority activate by the order of their insertion into the
    channel (when the start() method is called).
    """
    __slots__ = ("_channel", "_type", "callback", "_callback_mode",
                 "condition", "_priority", "owner", "match", "_deployed")

    CALLBACK_NO_ARGS = CALLBACK_NO_ARGS
    CALLBACK_TAKES_LISTENER = CALLBACK_TAKES_LISTENER
    CALLBACK_TAKES_SIGNAL = CALLBACK_TAKES_SIGNAL
    CALLBACK_TAKES_PAYLOAD = CALLBACK_TAKES_PAYLOAD
    CALLBACK_MODES = CALLBACK_MODES

    def __init__(self, channel, type, callback, callback_mode=None,
                 condition=None, priority=0.0, owner=None):
        self._channel = channel     # Channel - the channel where the listener is deployed
        self._type = type           # string (or None) - type of signal that triggers the listener
        self.callback = callback    # callable - function called when the listener is triggered
        self.callback_mode = callback_mode  # enum - specifies how to call the callback
        self.condition = condition  # callable - predicate used to filter matching signals
        self._priority = priority   # float - listener activation priority
        self.owner = owner          # the entity that created the listener
        self.match = None           # Signal - signal object that triggered the listener
        self._deployed = False      # bool - True if the listener is deployed to a channel

    def __info__(self):
        callback_arg = ("listener" if self.callback_mode == CALLBACK_TAKES_LISTENER else
                        "signal" if self.callback_mode == CALLBACK_TAKES_SIGNAL else
                        "signal.payload" if self.callback_mode == CALLBACK_TAKES_PAYLOAD else "")
        callback = "{}({})".format(callable_name(self.callback), callback_arg)
        condition = ("" if self.condition is None else
                     " if {}()".format(callable_name(self.condition)))
        owner = "" if self.owner is None else " by {}".format(self.owner)
        return ("|{}|{} -> {}{}, priority={:+.02f}"
                .format(self._type, condition, callback, owner, self._priority))

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, type):
        if self._deployed:
            self._channel._remove(self)
            self._type = type
            self._channel._insert(self)
        else:
            self._type = type

    @property
    def priority(self):
        return self._priority

    @priority.setter
    def priority(self, priority):
        if self._deployed:
            self._channel._remove(self)
            self._priority = priority
            self._channel._insert(self)
        else:
            self._priority = priority

    @property
    def deployed(self):
        return self._deployed

    @deployed.setter
    def deployed(self, deployed):
        if self._deployed and not deployed:
            self._channel._remove(self)
        elif not self._deployed and deployed:
            self._channel._insert(self)

    @property
    def callback_mode(self):
        mode = self._callback_mode
        return mode if mode is not None else self._channel.callback_mode

    @callback_mode.setter
    def callback_mode(self, mode):
        if mode is not None and mode not in CALLBACK_MODES:
            raise Exception("unrecognized callback mode: {!r}".format(mode))
        self._callback_mode = mode

    def start(self, force=False):
        if force or not self._deployed:
            self._channel._insert(self)

    def stop(self, force=False):
        if force or self._deployed:
            self._channel._remove(self)

    def _matches(self, signal):
        return self.condition is None or self.condition(signal)

    def _activate(self, signal):
        self.match = signal
        mode = self.callback_mode
        if mode == CALLBACK_NO_ARGS:
            self.callback()
        elif mode == CALLBACK_TAKES_LISTENER:
            self.callback(self)
        elif mode == CALLBACK_TAKES_SIGNAL:
            self.callback(signal)
        elif mode == CALLBACK_TAKES_PAYLOAD:
            self.callback(signal.payload)
        else:
            raise Exception("unexpected callback mode: {!r}".format(mode))
        self.match = None


@prettify_class
class Signal(object):
    """Signals are an instantaneous primitive that allows synchronizing several objects listening
    on the same channel. Signals activate listeners, which wait until a signal of matching type is
    emitted on the same channel.
    """
    ANY = "*"

    __slots__ = ("_channel", "type", "payload", "owner")

    def __init__(self, channel, type, payload=None, owner=None):
        if type == Signal.ANY:
            raise ValueError("signal type cannot be Signal.ANY ({!r})".format(Signal.ANY))
        self._channel = channel  # Channel to which the signal is associated
        self.type = type         # signal type (usually a string)
        self.payload = payload   # payload can be any Python object
        self.owner = owner       # the entity that emitted the signal

    def __info__(self):
        owner = "" if self.owner is None else " by {}".format(self.owner)
        payload = "" if self.payload is None else ": {}".format(self.payload)
        return "|{}|{}{}".format(self.type, owner, payload)

    def emit(self):
        self._channel._broadcast(self)


Channel.Signal = Signal
Channel.Listener = Listener


def example():
    import random

    def listener(l):
        pass  # print "{} activated by {}".format(l, l.match)

    c = Channel("sic", type_validation=True)
    c.register("foo")
    c.listen("foo", listener, owner="alice")
    c.emit("foo", owner="bob")

    for _ in xrange(10):
        c.listen(None, listener, priority=random.uniform(-1, +1),
                 condition=lambda s: isinstance(s.payload, dict) and "spam" in s.payload,
                 owner=random.choice(["charles", "david", "eva"]))

    try:
        c.emit("bar", payload={"spam": "eggs"})
    except ValueError, error:
        print error
        print "turning off channel type_validation..."
        c.type_validation = False
        c.emit("bar", payload={"spam": "eggs"})
    return c

from functools import partial
from utils.prettyrepr import prettify_class


@prettify_class
class FSM(object):
    """'Simple' class for finite state machines. The only constraint to the FSM is that you
    cannot attempt any state transition while exiting a state. This means that it is possible,
    while entering state A, to enter a second state B, and so on. Care must be taken with this
    usage though, since it leads to an error-prone order of execution. Here is the execution
    stack for the example:
        >> enter_A
            >> exit_A
            << exit_A
            >> enter_B
            << enter_B
        << enter_A
    Note that enter_A() only returns after exit_A() and enter_B() have been completely executed.
    Because of this, if you wish to enter another state from an entry function, make sure you do
    it only before returning, unless you really know what you're doing.
    """
    __info_attrs__ = ["state"]

    # changing these prefixes changes the names of the methods that are looked up for FSM
    # operations. It is not advised to change them unless it is really absolutely necessary.
    _enter_prefix = "enter_"
    _exit_prefix = "exit_"
    _transition_prefix = "transition_"

    # set this attribute in subclasses to the name of the initial state
    initial_state = None

    def __init__(self):
        self.__state = None     # current state (string)
        self.__exiting = False  # true when exiting a state (to prevent intermixed transitions)

    @property
    def state(self):
        return self.__state

    def init(self, *args, **kwargs):
        """Enter the machine's initial state."""
        return self.enter(self.initial_state, *args, **kwargs)

    def input(self, symbol, *args, **kwargs):
        """Feed a symbol to the state machine. The symbol is processed by the transition function
        defined by the current state (or the default transition function if the current state does
        not have a transition function). The transition function should return the name of the
        state the machine should transition to. Instead of a transition function, the class (or an
        individual FSM) may define a single transition target or a transition map. For example,
        the following three forms are equivalent:
            class Foo(FSM):
                def transition_default(self, symbol): return "xxx"   # transition function
            class Bar(FSM):
                transition_default = defaultdict(lambda: "xxx")      # transition map
            class Jez(FSM):
                transition_default = "xxx"                           # transition target

        If the target of a transition is None, nothing happens and the FSM remains in the same
        state (note that this is very different from exiting and entering the same state)."""
        if self.__state is None:
            raise ValueError("FSM state is undefined")
        try:
            transition = self.__get_state_attr(self._transition_prefix)
        except AttributeError:
            raise Exception("unable to find transition function or target")
        if callable(transition):
            new_state = transition(symbol)
        elif isinstance(transition, dict):
            new_state = transition[symbol]
        else:
            new_state = transition
        return None if new_state is None else self.enter(new_state, *args, **kwargs)

    __rrshift__ = input  # so that '3 >> fsm' is equivalent to 'fsm.input(3)'
    __lshift__ = input   # so that 'fsm << 3' is equivalent to 'fsm.input(3)'

    def enter(self, new_state, *args, **kwargs):
        """Enter a given state in the machine. Before calling the enter function of the new state,
        the exit function of the old state is executed. Note that the exit function is optional.
        If no exit function is found, the next state's enter function, if defined, will be called
        immediately."""
        if self.__exiting:
            raise Exception("cannot enter new state while exiting current state")
        if self.__state is not None:
            self.exit()
        if new_state is not None:
            self.__state = new_state
            return self.__call_transition_fnc(self._enter_prefix, *args, **kwargs)
        return None

    def exit(self):
        """Exit current state. Calls the current state's exit function and sets the FSM's state to
        None."""
        if self.__exiting:
            raise Exception("duplicate attempt to exit current state")
        if self.__state is not None:
            self.__exiting = True
            result = self.__call_transition_fnc(self._exit_prefix)
            self.__exiting = False
            self.__state = None
            return result
        return None

    def __get_state_attr(self, prefix):
        """Get an attribute of the FSM formed by the argument prefix followed by the string form
        of the current state. If the attribute lookup fails, the prefix plus "default" are looked
        up and returned (if possible). Attribute error is raised if the state attribute is not
        available for both the current state and the default state."""
        try:
            return getattr(self, prefix + str(self.__state))
        except AttributeError:
            return getattr(self, prefix + "default")

    def __call_transition_fnc(self, prefix, *args, **kwargs):
        """Fetch the enter()/exit() function for the current state (or the default one) and call
        it, returning the function's result(s). If the function doesn't exist, None is returned."""
        try:
            transition_fnc = self.__get_state_attr(prefix)
        except AttributeError:
            return None
        else:
            return transition_fnc(*args, **kwargs)

    @staticmethod
    def input_shortcut(symbol, name=None):
        """This static method creates a shortcut method to input a given symbol into an FSM. The
        function can then be added to an FSM class to be used as a method."""
        def input_method(self, *args, **kwargs):
            return self.input(symbol, *args, **kwargs)
        input_method.__name__ = str(name) if name is not None else ("input_" + str(symbol))
        input_method.__doc__ = "Shortcut method to feed symbol '%s' into the FSM." % str(symbol)
        return input_method

    # --------------------------------------------------------------------------
    # Default FSM protocol (uses FSM_BoundState objects)
    def enter_default(self, *args, **kwargs):
        bound_state = self.get_bound_state()
        if isinstance(bound_state, FSM_BoundState):
            return bound_state.enter(*args, **kwargs)
        return None

    def exit_default(self):
        bound_state = self.get_bound_state()
        if isinstance(bound_state, FSM_BoundState):
            return bound_state.exit()
        return None

    def transition_default(self, symbol):
        bound_state = self.get_bound_state()
        if isinstance(bound_state, FSM_BoundState):
            return bound_state.transition(symbol)
        return None

    def get_bound_state(self, name=None):
        """This is an auxiliary method used when using the default FSM protocol. This method should
        return a FSM_BoundState object, to be used by the default protocol methods enter_default(),
        exit_default(), and transition_default(). The default behavior of get_bound_state() is to
        retrieve the FSM_BoundState object as an attribute of the FSM, using the builtin getattr().
        Accessing bound states is abstracted into a method to allow FSM subclasses to store their
        FSM_BoundState objects in other ways and retrieve them using this method."""
        if name is None:
            name = self.__state
        return None if name is None else getattr(self, name, None)


class FSM_State(object):
    # --------------------------------------------------------------------------
    # Function/method decorators
    def __init__(self, enter_fnc=None, exit_fnc=None, transition_fnc=None):
        self.enter_fnc = enter_fnc
        self.exit_fnc = exit_fnc
        self.transition_fnc = transition_fnc

    def on_enter(self, enter_fnc):
        return type(self)(enter_fnc, self.exit_fnc, self.transition_fnc)

    def on_exit(self, exit_fnc):
        return type(self)(self.enter_fnc, exit_fnc, self.transition_fnc)

    def on_transition(self, transition_fnc):
        return type(self)(self.enter_fnc, self.exit_fnc, transition_fnc)

    # --------------------------------------------------------------------------
    # Descriptor protocol
    def __get__(self, fsm, cls):
        if fsm is None:
            return self
        try:
            bound_state = fsm.__state[self]
        except AttributeError:
            bound_state = self.bound_to(fsm)
            fsm.__state = {self: bound_state}
        except KeyError:
            bound_state = self.bound_to(fsm)
            fsm.__state[self] = bound_state
        return bound_state

    # --------------------------------------------------------------------------
    # State methods
    def bound_to(self, fsm):
        return FSM_BoundState(fsm, self.enter_fnc, self.exit_fnc, self.transition_fnc)

    def enter(self, fsm, *args, **kwargs):
        enter_fnc = self.enter_fnc
        if enter_fnc is not None:
            return enter_fnc(fsm, *args, **kwargs)

    def exit(self, fsm):
        exit_fnc = self.exit_fnc
        if exit_fnc is not None:
            return exit_fnc(fsm)

    def transition(self, fsm, symbol):
        transition_fnc = self.transition_fnc
        if transition_fnc is not None:
            return transition_fnc(fsm, symbol)

    @staticmethod
    def transition_fnc_from_mapping(transition_mapping):
        """A factory for state transition functions. The function wraps a transition mapping, i.e.
        something that provides a __getitem__() method, such as a plain dictionary. Since the
        transition function is called with two arguments (the FSM and a symbol), we cannot use
        dict.__getitem__ directly, and that's the reason for creating a wrapper function.
        Intended use:
            class foo(FSM):
                @FSM.State
                def bar(self):
                    print "entered", self.state

                bar.transition_fnc = FSM.State.transition_fnc_from_mapping({"foo": "bar"})
        The mapping associated to the transition function can be accessed through the function's
        'mapping' attribute."""
        def transition_fnc(fsm, symbol):
            try:
                return transition_mapping[symbol]
            except KeyError:
                raise KeyError("unable to find transition for symbol: %r" % (symbol,))
        # make transition mapping available through the function
        transition_fnc.mapping = transition_mapping
        return transition_fnc


class FSM_BoundState(object):
    """A state associated to a particular FSM. When its methods (enter(), exit(), and transition())
    are called, the FSM is automatically passed as the first argument."""
    enter_fnc = None
    exit_fnc = None
    transition_fnc = None

    def __init__(self, fsm, enter_fnc=None, exit_fnc=None, transition_fnc=None):
        self.fsm = fsm
        if enter_fnc is not None:
            self.enter_fnc = enter_fnc
        if exit_fnc is not None:
            self.exit_fnc = exit_fnc
        if transition_fnc is not None:
            self.transition_fnc = transition_fnc

    def enter(self, *args, **kwargs):
        enter_fnc = self.enter_fnc
        if enter_fnc is not None:
            return enter_fnc(self.fsm, *args, **kwargs)

    def exit(self):
        exit_fnc = self.exit_fnc
        if exit_fnc is not None:
            return exit_fnc(self.fsm)

    def transition(self, symbol):
        transition_fnc = self.transition_fnc
        if transition_fnc is not None:
            return transition_fnc(self.fsm, symbol)


class FSM_Driver(object):
    """This class allows feeding input symbols to the FSM as if they were methods of the driver
    object. For example:
        fsm.driver.run(cpu=60)
            is equivalent to
        fsm.input("run", cpu=60)
    Actually, attribute access on the driver object returns a partial method call to input() on
    the FSM where the input symbol is the attribute name. The remaining arguments (in this case,
    'cpu') are passed afterwards when the partial object is actually called."""
    def __init__(self, fsm):
        self.fsm = fsm

    def __input_symbol__(self, symbol):
        return partial(self.fsm.input, symbol)

    __getattr__ = __input_symbol__
    __getitem__ = __input_symbol__


FSM.State = FSM_State
FSM.BoundState = FSM_BoundState
FSM.Driver = FSM_Driver


def _example1():
    import string
    import random
    import types

    a = FSM()
    a.transition_default = string.uppercase.__getitem__
    for i in xrange(len(string.uppercase)):
        fnc = a.input_shortcut(i)
        setattr(a, fnc.__name__, types.MethodType(fnc, a, FSM))
    a.enter(string.uppercase[0])
    for _ in xrange(10):
        getattr(a, "input_"+str(random.randrange(len(string.uppercase))))()
    return a


def _example2():
    class foo(FSM):
        initial_state = "bar"

        @FSM.State
        def bar(self):
            print "bar"

        @bar.on_transition
        def bar(self, symbol):
            if symbol == "baz":
                print "OMG!"
                return "fez"
            return None

        @FSM.State
        def fez(self):
            print "fez"

        fez.transition_fnc = FSM.State.transition_fnc_from_mapping({"foo": "bar", "gif": "fez"})
        baz = FSM.input_shortcut("baz")
        # --- end of class foo

    f = foo()  # create instance, no state entered
    f.init()   # FSM enters state 'bar'
    f.baz()    # FSM is fed 'baz', transitions into state 'fez'
    return f

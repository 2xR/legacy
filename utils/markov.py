from collections import deque
from itertools import chain
import random

from utils import treedict
from utils.fsm import FSM
from utils.prettyrepr import prettify_class


@prettify_class
class MC_BoundState(FSM.BoundState):
    """A bound state class for Markov Chains."""
    def __init__(self, fsm, name):
        FSM.BoundState.__init__(self, fsm)
        self.name = name
        self.transitions = {}  # {history<tuple(str)>: {next<str>: weight<real>}}

    def __info__(self):
        transitions = "terminal" if self.is_terminal else len(self.transitions)
        return "{} <{}>".format(self.name, transitions)

    @property
    def is_terminal(self):
        return len(self.transitions) == 0

    def record_transition(self, next_state, history=(), weight=1.0):
        history = tuple(history)
        prev_weight = treedict.getdefault(self.transitions, history, next_state, 0.0)
        treedict.set(self.transitions, history, next_state, prev_weight+weight)

    def transition_fnc(self, mc, rng):
        substate = self.transitions[tuple(mc.history)]
        x = rng.uniform(0.0, sum(substate.itervalues()))
        for next_state, weight in substate.iteritems():
            if x <= weight:
                return next_state
            x -= weight
        raise Exception("something went awfully bad... insert coin and try again")


class MarkovChain(FSM):
    def __init__(self, memory=0):
        FSM.__init__(self)
        self.history = deque(maxlen=memory)
        self.name_to_state = {}

    @property
    def memory(self):
        return self.history.maxlen

    def add_state(self, name, error_on_duplicate=True):
        try:
            state = self.name_to_state[name]
        except KeyError:
            state = self.name_to_state[name] = MC_BoundState(self, name)
        else:
            if error_on_duplicate:
                raise NameError("duplicate state name -- {}".format(name))
        return state

    def get_bound_state(self, name=None):
        if name is None:
            name = self.state
        return self.name_to_state[name]

    @classmethod
    def from_sequence(cls, sequence, memory=0):
        """Build a Markov Chain from a sequence of states."""
        sequence = iter(sequence)
        history = deque(maxlen=memory)
        chain = cls(memory=memory)
        chain.initial_state = curr_state = sequence.next()
        for next_state in sequence:
            chain.record_transition(curr_state, next_state, history)
            if memory > 0:
                history.append(curr_state)
            curr_state = next_state
        return chain

    def record_transition(self, curr_state, next_state, history=(), weight=1.0):
        """This method is used when building the Markov chain. It records a certain transition,
        with an optional sequence of previous states (that should be of size no larger than the
        chain's memory), and assigns a given weight to the transition.
        NOTE: new state objects are created and added to the chain for any state names that are
        not already in the chain. If you want to use custom state objects, create and add them to
        the chain before using this method."""
        if len(history) > self.memory:
            raise ValueError("length of history information exceeds memory of Markov chain")
        # create new state objects for any names that are not found in the chain
        for state in chain(history, [curr_state, next_state]):
            self.add_state(state, error_on_duplicate=False)
        # and finally record the transition
        current = self.get_bound_state(curr_state)
        current.record_transition(next_state, history, weight)

    def init(self):
        self.history.clear()
        return FSM.init(self)

    def step(self, rng=random, *args, **kwargs):
        return self.input(rng, *args, **kwargs)

    def exit(self):
        if self.history.maxlen > 0 and self.state is not None:
            self.history.append(self.state)
        return FSM.exit(self)

    def random_walk(self, initial_state=None, rng=random):
        """Starting from the initial state, do a random walk in the Markov Chain using 'rng'. The
        random walk ends when a terminal state is reached."""
        if initial_state is not None:
            self.initial_state = initial_state
        self.init()
        yield self.state
        while not self.get_bound_state().is_terminal:
            self.step(rng)
            yield self.state


def _test(filepath=__file__, memory=1):
    import string
    import itertools

    translation = string.maketrans(string.punctuation, " " * len(string.punctuation))
    with open(filepath) as istream:
        text = istream.read()
    words = text.lower().translate(translation).split()
    del text
    mc = MarkovChain.from_sequence(words, memory=memory)
    it = mc.random_walk()
    mc.generate_text = lambda n=100: " ".join(word for _, word in itertools.izip(xrange(n), it))
    print "Sample output for Markov Chain with memory=%d" % memory
    print "Generating 100 words..."
    print mc.generate_text(100)
    return mc

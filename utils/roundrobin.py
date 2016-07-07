def constant_policy(x):
    def policy(i):
        return x
    policy.__name__ = "constant_policy_" + str(x)
    return policy


def linear_policy(i):
    return i + 1


class RoundRobin(object):
    """RoundRobin objects can be used to visit a sequence circularly using a regular round-robin
    policy or any other policy function. The role of the policy function is to determine the number
    of visits to a given index in the sequence, e.g. a regular round-robin policy would simply
    return 1 regardless of the index being visited. The predefined linear_policy() assigns more
    visits to larger indices using a linear expression (i+1). Users can provide their own visit
    policy functions, taking a single argument (the index) and returning the number of times that
    the argument index should be visited. Note that the policy needn't be deterministic.
    """
    __slots__ = ("sequence", "visit_policy", "index", "visits", "max_visits")

    def __init__(self, sequence, visit_policy=constant_policy(1)):
        self.sequence = sequence
        self.visit_policy = visit_policy
        self.index = -1
        self.visits = 0
        self.max_visits = 0

    def next(self):
        return self.sequence[self.next_index()]

    def next_index(self):
        if self.visits >= self.max_visits:
            i = self.advance_index()
        else:
            i = self.index
            if i >= len(self.sequence):
                self.index = -1
                i = self.advance_index()
        self.visits += 1
        return i

    def advance_index(self):
        """Move the index forward after we reached the maximum number of visits to the current
        index."""
        n = len(self.sequence)
        if n == 0:
            self.index = -1
            self.visits = 0
            self.max_visits = 0
            return None
        i = self.index
        v = 0
        p = self.visit_policy
        while v <= 0:
            i = (i + 1) % n
            v = p(i)
        self.index = i
        self.visits = 0
        self.max_visits = v
        return i

    def force_advance_index(self):
        """This forces the next call to next_index() to advance the index by setting the number of
        maximum visits to the current index to zero."""
        self.max_visits = 0

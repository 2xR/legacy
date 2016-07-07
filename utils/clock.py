from contextlib import contextmanager
from time import clock

from utils.prettyrepr import prettify_class
from utils.taggablelist import TaggableList
from utils.misc import INF


@prettify_class
class Clock(object):
    """Clock object for CPU tracking. To track the CPU time of a function just call it in a
    tracking() context block, like:
        clock = Clock()
        with clock.tracking():
            do_stuff()
        print "Elapsed CPU time:", clock.total
    """
    def __init__(self, limit=INF, start=False):
        self._start = None
        self._cpu = 0.0
        self._tracks = 0
        self.checkpoints = TaggableList()
        self.intervals = TaggableList()
        self.limit = limit
        if start:
            self.start()

    def __info__(self):
        return "%fs [limit=%s, %d tracks]" % (self.total, self.limit, self._tracks)

    @property
    def active(self):
        return self._tracks > 0

    @property
    def total(self):
        if self._tracks > 0:
            return self._cpu + (clock() - self._start)
        else:
            return self._cpu

    @property
    def remaining(self):
        return self.limit - self.total

    def reset(self, force=False):
        if not force and self._tracks > 0:
            raise Exception("cannot reset clock - active tracks remaining")
        self._start = None
        self._cpu = 0.0
        self._tracks = 0
        self.checkpoints.clear()
        self.intervals.clear()
        self.limit = INF

    clear = reset

    def start(self):
        if self._tracks == 0:
            self._start = clock()
        self._tracks += 1

    def stop(self):
        if self._tracks == 0:
            raise ValueError("cannot stop Clock - no active tracks remaining")
        self._tracks -= 1
        if self._tracks == 0:
            self._cpu += clock() - self._start
            self._start = None

    @contextmanager
    def tracking(self):
        self.start()
        try:
            yield self
        except BaseException as error:
            self.stop()
            raise error
        else:
            self.stop()

    def checkpoint(self, *tags):
        """Add a checkpoint to the clock. This will take a reading of the current total cpu and
        append it to the 'checkpoints' list, and also compute the difference between this and the
        previous checkpoint and append it to the 'intervals' list. When the first checkpoint is
        taken, the checkpoint itself is added to the 'intervals' list (i.e. the previous checkpoint
        is t=0).
        Since 'checkpoints' and 'intervals' lists are TaggableList objects, a number of tags may
        optionally be associated with the checkpoint and interval, making it easier to later refer
        to them without actually knowing their indices in the list."""
        checkpoints = self.checkpoints
        checkpoints.append(self.total, tags=tags)
        if len(checkpoints) > 1:
            self.intervals.append(checkpoints[-1] - checkpoints[-2], tags=tags)
        else:
            self.intervals.append(checkpoints[-1], tags=tags)

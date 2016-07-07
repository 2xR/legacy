from __future__ import absolute_import
from itertools import imap
from bisect import bisect_left
from operator import itemgetter
from collections import deque
from time import time
from sys import stdout
import threading

from utils.misc import callable_name, getitem, INF
from utils.deque import deque_insort_right, deque_pop
from utils.prettyrepr import prettify_class


def make_log_fnc(ostream=stdout):
    """Log function factory. The returned log function writes its output into the argument stream
    (a file-like object, default is sys.stdout). The returned function is appropriate to be used
    as a log function for the calendar object."""
    def log_fnc(calendar, event):
        ostream.write("[{:>10.03f}] {}\n".format(calendar.time, event))
    return log_fnc


@prettify_class
class Calendar(object):
    """Base class for calendar types, providing basic facilities for scheduling events and
    managing time."""
    __slots__ = ("_time", "_events", "log_fnc")
    default_log_fnc = make_log_fnc(stdout)
    make_log_fnc = staticmethod(make_log_fnc)

    def __init__(self, time=0.0, log_fnc=default_log_fnc):
        self._time = time
        self._events = deque()
        self.log_fnc = log_fnc

    def __info__(self):
        return "time={:.03f}, events={}".format(self._time, len(self._events))

    def clear(self, time=0.0):
        self._time = time
        self._events.clear()

    reset = clear

    def get_time(self):
        return self._time

    def set_time(self, time):
        if time < self._time:
            raise ValueError("invalid attempt to go back in time")
        log = self.log_fnc
        events = self._events
        while len(events) > 0:
            next_date, _, next_event = events[0]
            if next_date > time:
                break
            self._time = next_date
            events.popleft()
            if log is not None:
                log(self, next_event)
            next_event._deployed = False
            next_event._activate()
        self._time = time

    time = property(get_time, set_time)

    def advance_time(self, delta):
        self.set_time(self._time + delta)

    @property
    def dates(self):
        return imap(itemgetter(0), self._events)

    @property
    def events(self):
        return imap(itemgetter(2), self._events)

    def step(self, n=1):
        """Advance 'n' events in the calendar."""
        log = self.log_fnc
        events = self._events
        i = None
        for i in xrange(1, n+1):
            if len(events) == 0:
                break
            next_date, _, next_event = events.popleft()
            self._time = next_date
            if log is not None:
                log(self, next_event)
            next_event._deployed = False
            next_event._activate()
        return i

    def jump(self, n=1):
        """Advance 'n' instants/dates in the calendar."""
        events = self._events
        i = None
        for i in xrange(1, n+1):
            if len(events) == 0:
                break
            self.set_time(events[0][0])
        return i

    def schedule_at(self, date, callback, priority=0.0, owner=None):
        """Schedule a new event at a specific 'date'."""
        event = Event(self, date, callback, priority, owner)
        event.schedule()
        return event

    def schedule_after(self, delta, callback, priority=0.0, owner=None):
        """Schedule a new event at the current time plus 'delta'."""
        return self.schedule_at(self._time + delta, callback, priority, owner)

    # --------------------------------------------------------------------------
    # private methods for insertion and removal of events
    def _insert(self, event):
        if event._calendar is not self:
            raise ValueError("event is not associated with this calendar")
        if event._deployed:
            raise ValueError("duplicate attempt to deploy event")
        if event._date < self._time:
            raise ValueError("unable to schedule event at previous date")
        deque_insort_right(self._events, (event._date, event._priority, event))
        event._deployed = True

    def _remove(self, event):
        if event._calendar is not self:
            raise ValueError("event is not associated with this calendar")
        if not event._deployed:
            raise ValueError("event is not deployed")
        index = bisect_left(self._events, event)
        assert self._events[index] == (event._date, event._priority, event)
        deque_pop(self._events, index)
        event._deployed = False


class RealTimeCalendar(Calendar):
    """A calendar type that can execute events in (approximate) real time or modified (compressed
    or expanded) time using a multiplier. It uses an auxiliary thread that advances time in the
    calendar at each iteration, until pause() is called or a time limit is reached."""
    __slots__ = ("_speed", "_limit", "_running", "_interrupt")

    def __init__(self, speed=1.0, time=0.0, log_fnc=Calendar.default_log_fnc):
        Calendar.__init__(self, time, log_fnc)
        self._speed = None
        self._limit = INF
        self._running = False
        self._interrupt = threading.Event()
        self.speed = speed

    def __info__(self):
        fmt = "time={:.03f}, events={}, running={}, speed={:.03f}, limit={:03f}"
        return fmt.format(self._time, len(self._events), self._running, self._speed, self._limit)

    def clear(self, time=0.0):
        if self._running:
            raise Exception("cannot clear() calendar while it is running")
        Calendar.clear(self, time)

    reset = clear

    def _insert(self, event):
        if self._running and (len(self._events) == 0 or event._date < self._events[0][0]):
            self._interrupt.set()
        Calendar._insert(self, event)

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, speed):
        if speed <= 0.0:
            raise ValueError("real time calendar speed must be a positive real number")
        self._speed = speed

    @property
    def limit(self):
        return self._limit

    @limit.setter
    def limit(self, limit):
        if limit < self._time:
            raise ValueError("cannot set limit to past date")
        self._limit = limit

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, running):
        if self._running and not running:
            self.pause()
        elif not self._running and running:
            self.run()

    def run(self, delta=INF, until=INF, speed=None):
        """Advance the calendar in real time (or scaled real time) until pause() is called or the
        specified time limit is reached in the calendar."""
        if self._running:
            raise ValueError("calendar is already running")
        if speed is not None:
            self.speed = speed
        self.limit = min(until, self._time + delta)
        threading.Thread(target=self._run).start()

    def pause(self):
        """If the calendar is running, pause it."""
        if self._running:
            self._running = False
            self._interrupt.set()

    def _run(self):
        events = self._events
        self._running = True
        while self._running and self._time < self._limit:
            # compute the time until the next event or the limit, whichever occurs first
            if len(events) > 0:
                timeout = min(self._limit, events[0][0]) - self._time
            else:
                timeout = self._limit - self._time
            # scale the timeout according to the calendar's speed
            timeout /= self._speed
            # wait until the timeout passes or the _interrupt event is set
            t0 = time()
            self._interrupt.wait(timeout)
            if self._interrupt.is_set():
                self._interrupt.clear()
            t1 = time()
            self.advance_time((t1 - t0) * self._speed)
        self._running = False


@prettify_class
class Event(object):
    """An event executes a given callback function when its date is reached in the calendar.
    Events should be created through the Calendar.schedule_at() method."""
    __slots__ = ("_calendar", "_date", "callback", "_priority", "owner", "_deployed")

    def __init__(self, calendar, date, callback, priority=0.0, owner=None):
        self._calendar = calendar  # Calendar object
        self._date = date          # event date
        self.callback = callback   # callable executed when the event's date is reached
        self._priority = priority  # for breaking ties, lower priority activates first
        self.owner = owner         # any object that may be helpful for debugging
        self._deployed = False     # True when the event is in a Calendar

    def __info__(self):
        callback = callable_name(self.callback)
        owner = "" if self.owner is None else " by {}".format(self.owner)
        return "t={:.03f} -> {}(){}, priority={:+.02f}".format(self.date, callback,
                                                               owner, self.priority)

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, date):
        if self._deployed:
            self._calendar._remove(self)
            self._date = date
            self._calendar._insert(self)
        else:
            self._date = date

    @property
    def priority(self):
        return self._priority

    @priority.setter
    def priority(self, priority):
        if self._deployed:
            self._calendar._remove(self)
            self._priority = priority
            self._calendar._insert(self)
        else:
            self._priority = priority

    @property
    def deployed(self):
        return self._deployed

    @deployed.setter
    def deployed(self, deployed):
        if self._deployed and not deployed:
            self._calendar._remove(self)
        elif not self._deployed and deployed:
            self._calendar._insert(self)

    def schedule(self):
        self._calendar._insert(self)

    def cancel(self):
        self._calendar._remove(self)

    def _activate(self):
        self.callback()


def example(n=20):
    from random import random

    calendar = RealTimeCalendar()

    def chain():
        next_date = getitem(calendar.events, 0).date
        new_event_date = calendar.time + random()
        if new_event_date < next_date:
            print "new next event date {} -> {}".format(next_date, new_event_date)
        else:
            print "maintaining next event date at {}".format(next_date)
        calendar.schedule_at(new_event_date, chain)

    # set up two infinite chains of events
    for _ in xrange(2):
        calendar.schedule_after(random(), chain)
    return calendar

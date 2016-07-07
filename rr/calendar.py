from __future__ import absolute_import
import collections
import itertools
import bisect
import operator
import logging

from . import pretty, deque


@pretty.klass
class Calendar(object):
    """
    Base class for calendar types, providing basic facilities for scheduling events and managing
    time. An event is nothing more than a callback that is executed at a given date.
    """
    default_logger = logging.getLogger(__name__)

    def __init__(self, time=0.0, logger=default_logger):
        self._time = time  # current time
        self._queue = collections.deque()  # sorted deque of (time, priority, event) tuples
        self.logger = logger  # logging.Logger or object with similar api

    def __info__(self):
        return "time={:.03f}, events={}".format(self._time, len(self._queue))

    def clear(self, time=0.0):
        self._time = time
        self._queue.clear()

    reset = clear

    def __iter__(self):
        """
        Iteration over a calendar consumes and activates events in chronological order. Yields
        Event objects after they've been activated. Note that this iterator keeps going until the
        calendar becomes empty (which may never occur!), so care must be taken if using this as
        in 'list(calendar)'.
        """
        info = self.logger.info
        queue = self._queue
        while len(queue) > 0:
            date, _, event = queue.popleft()
            info(event)
            self._time = date
            event._activate()
            yield event

    @property
    def time(self):
        """
        The calendar's 'time' can be set (forward only!), consuming and activating events in
        chronological order.
        """
        return self._time

    @time.setter
    def time(self, time):
        if time < self._time:
            raise ValueError("invalid attempt to go back in time")
        queue = self._queue
        if time >= queue[0][0]:
            for _ in self:
                if time < queue[0][0]:
                    break
        self._time = time

    @property
    def dates(self):
        return itertools.imap(operator.itemgetter(0), self._queue)

    @property
    def events(self):
        return itertools.imap(operator.itemgetter(2), self._queue)

    def step(self, n=1):
        """Advance 'n' events in the calendar. Returns the number of events consumed."""
        i = None
        for i, _ in enumerate(self, start=1):
            if i >= n:
                break
        return i

    def jump(self, n=1):
        """Advance 'n' instants/dates in the calendar. Returns the number of instants consumed."""
        queue = self._queue
        i = None
        for i in xrange(1, n+1):
            if len(queue) == 0:
                break
            self.time = queue[0][0]
        return i

    def schedule_at(self, date, callback, priority=0.0):
        """Schedule a new event at a specific 'date'."""
        event = Event(self, date, callback, priority)
        event.schedule()
        return event

    def schedule_after(self, delta, callback, priority=0.0):
        """Schedule a new event at the current time plus 'delta'."""
        return self.schedule_at(self._time + delta, callback, priority)

    # ----------------------------------------------------------------------------------------------
    # Internal methods for insertion and removal of events
    def _insert(self, event):
        if event._calendar is not self:
            raise ValueError("event is not associated with this calendar")
        if event._date < self._time:
            raise ValueError("unable to schedule event at previous date")
        deque.insort_right(self._queue, (event._date, event._priority, event))

    def _remove(self, event):
        if event._calendar is not self:
            raise ValueError("event is not associated with this calendar")
        start_index = bisect.bisect_left(self._queue, (event._date, event._priority, None))
        for index in xrange(start_index, len(self._queue)):
            t, _, e = self._queue[index]
            if e is event:
                return deque.pop(self._queue, index)
            if t != event._date:
                break
        raise ValueError("event not found in calendar")


@pretty.klass
class Event(object):
    """
    An event executes a given callback function when its date is reached in the calendar. Events
    should be created through the Calendar.schedule_XXX() methods.
    """
    def __init__(self, calendar, date, callback, priority=0.0):
        self._calendar = calendar  # Calendar object
        self._date = date  # event date
        self.callback = callback   # callable executed when the event's date is reached
        self._priority = priority  # for breaking ties, lower priority activates first
        self._deployed = False     # True when the event is in a Calendar

    def __info__(self):
        return "t={:.03f} -> {}(), priority={:+.02f}".format(
            self.date, self.callback.__name__, self.priority)

    @property
    def date(self):
        """
        The 'date' property defines the calendar position of the event. This property allows
        changing the event's date even if it is deployed. In such cases, the event is removed and
        re-inserted in the calendar with the updated date.
        """
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
        """
        The 'priority' property defines the order by which events with the same date are
        activated. This property allows changing the event's priority even if it is deployed. In
        such cases, the event is removed and re-inserted in the calendar with the updated
        priority value.
        """
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
        """
        The 'deployed' boolean property automatically manages the insertion/removal of the event
        into the calendar.
        """
        return self._deployed

    @deployed.setter
    def deployed(self, deployed):
        deployed = bool(deployed)
        if self._deployed and not deployed:
            self._calendar._remove(self)
        elif not self._deployed and deployed:
            self._calendar._insert(self)
        self.deployed = deployed

    def schedule(self):
        """
        Enqueue the event in a calendar to be activated at a later date. Will raise an exception
        if the event is already deployed.
        """
        if self._deployed:
            raise ValueError("cannot schedule: event is already deployed")
        self._calendar._insert(self)
        self._deployed = True

    def cancel(self):
        """
        Remove the event from the calendar. Will raise an exception if the event is not deployed.
        """
        if not self._deployed:
            raise ValueError("cannot cancel: event is not deployed")
        self._calendar._remove(self)
        self._deployed = False

    def activate(self):
        """
        Manually activate the event. If the event is deployed, it will be canceled before
        executing the callback function.
        """
        if self._deployed:
            self.cancel()
        self._activate()

    def _activate(self):
        """
        Internal method. This sets the _deployed flag to False and invokes the callback function.
        """
        self._deployed = False
        self.callback()


# class RealTimeCalendar(Calendar):
#     """
#     A calendar type that can execute events in (approximate) real time or modified (compressed or
#     expanded) time using a multiplier. It uses an auxiliary thread that advances time in the
#     calendar at each iteration, until pause() is called or a time limit is reached.
#     """
#     def __init__(self, speed=1.0, time=0.0, log_fnc=Calendar.default_log_fnc):
#         Calendar.__init__(self, time, log_fnc)
#         self._speed = None
#         self._limit = Inf
#         self._running = False
#         self._interrupt = threading.Event()
#         self.speed = speed
#
#     def __info__(self):
#         fmt = "time={:.03f}, events={}, running={}, speed={:.03f}, limit={:03f}"
#         return fmt.format(self._time, len(self._queue), self._running, self._speed, self._limit)
#
#     def clear(self, time=0.0):
#         if self._running:
#             raise Exception("cannot clear() calendar while it is running")
#         Calendar.clear(self, time)
#
#     reset = clear
#
#     def _insert(self, event):
#         if self._running and (len(self._queue) == 0 or event._date < self._queue[0][0]):
#             self._interrupt.set()
#         Calendar._insert(self, event)
#
#     @property
#     def speed(self):
#         return self._speed
#
#     @speed.setter
#     def speed(self, speed):
#         if speed <= 0.0:
#             raise ValueError("real time calendar speed must be a positive real number")
#         self._speed = speed
#
#     @property
#     def limit(self):
#         return self._limit
#
#     @limit.setter
#     def limit(self, limit):
#         if limit < self._time:
#             raise ValueError("cannot set limit to past date")
#         self._limit = limit
#
#     @property
#     def running(self):
#         return self._running
#
#     @running.setter
#     def running(self, running):
#         if self._running and not running:
#             self.pause()
#         elif not self._running and running:
#             self.run()
#
#     def run(self, delta=Inf, until=Inf, speed=None):
#         """Advance the calendar in real time (or scaled real time) until pause() is called or the
#         specified time limit is reached in the calendar."""
#         if self._running:
#             raise ValueError("calendar is already running")
#         if speed is not None:
#             self.speed = speed
#         self.limit = min(until, self._time + delta)
#         threading.Thread(target=self._run).start()
#
#     def pause(self):
#         """If the calendar is running, pause it."""
#         if self._running:
#             self._running = False
#             self._interrupt.set()
#
#     def _run(self):
#         events = self._queue
#         self._running = True
#         while self._running and self._time < self._limit:
#             # compute the time until the next event or the limit, whichever occurs first
#             if len(events) > 0:
#                 timeout = min(self._limit, events[0][0]) - self._time
#             else:
#                 timeout = self._limit - self._time
#             # scale the timeout according to the calendar's speed
#             timeout /= self._speed
#             # wait until the timeout passes or the _interrupt event is set
#             t0 = time.time()
#             self._interrupt.wait(timeout)
#             if self._interrupt.is_set():
#                 self._interrupt.clear()
#             t1 = time.time()
#             self.advance_time((t1 - t0) * self._speed)
#         self._running = False


def example(n=2):
    import random

    calendar = Calendar()

    def event_chain():
        calendar.schedule_after(random.random(), event_chain)
        print "t = {}".format(calendar.time)
        print "\n".join(map(str, calendar.events))

    for _ in xrange(n):
        calendar.schedule_after(random.random(), event_chain)
    return calendar

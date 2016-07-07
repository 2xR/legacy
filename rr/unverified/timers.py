class Timer(object):
    def __init__(self, table, callback, delay, repeat):
        self.table = table
        self.callback = callback
        self.delay = delay
        self.repeat = repeat
        self.running = False
        self.finished = False

    def start(self):
        if self.finished:
            raise Exception("timer is finished")
        if not self.running:
            self.running = True
            self._start()

    def _start(self):
        raise NotImplementedError()

    def pause(self):
        if self.finished:
            raise Exception("timer is finished")
        if self.running:
            self.running = False
            self._pause()

    def _pause(self):
        raise NotImplementedError()

    def resume(self):
        if self.finished:
            raise Exception("timer is finished")
        if not self.running:
            self.running = True
            self._resume()

    def _resume(self):
        self._start()

    def finish(self):
        if self.finished:
            raise Exception("timer is already finished")
        self.finished = True
        self._finish()
        self.table.remove(self)

    def _finish(self):
        if self.running:
            self._pause()


class TimerTable(object):
    """This class can be used as an abstraction layer over the different APIs for scheduling
    callbacks in a GUI toolkit, game engine, or the like. The Timer class should be subclassed
    and a TimerTable can be used to manage all timers using the same API despite using a different
    GUI or game engine. Check out kivyx.timers for an example Timer class for the Kivy framework.
    """
    def __init__(self, timer_cls):
        self.timer_cls = timer_cls
        self.timers = set()
        self.saved = set()
        self.running = True

    def clear(self):
        for timer in list(self.timers):
            timer.finish()
        if len(self.timers) > 0:
            raise Exception("timer table should be empty")
        self.saved.clear()

    def schedule(self, callback, delay, repeat=True):
        timer = self.timer_cls(self, callback, delay, repeat)
        self.timers.add(timer)
        if self.running:
            timer.start()
        else:
            self.saved.add(timer)
        return timer

    def schedule_interval(self, callback, delay):
        return self.schedule(callback, delay, True)

    def schedule_once(self, callback, delay):
        return self.schedule(callback, delay, False)

    def remove(self, timer):
        self.timers.remove(timer)
        self.saved.discard(timer)

    def pause(self):
        if self.running:
            for timer in self.timers:
                if timer.running:
                    timer.pause()
                    self.saved.add(timer)
            self.running = False

    def resume(self):
        if not self.running:
            for timer in self.saved:
                timer.resume()
            self.saved.clear()
            self.running = True

    def toggle(self):
        (self.pause if self.running else self.resume)()


# ---------------------------------------------------------
# Example implementation of timers and timer tables using the
# event scheduling facilities provided by utils.scheduling
# ---------------------------------------------------------
from utils.calendar import Calendar


class TimerEvent(Timer):
    """Example timer implementation based on utils.scheduling.Event."""
    def _start(self):
        self.remaining_time = self.delay
        self._resume()

    def _resume(self):
        self.deployment_time = self.table.calendar.time
        self.event = self.table.calendar.schedule_after(self.remaining_time, self._exec)

    def _exec(self):
        self.callback()
        self.running = False
        if self.repeat:
            self.start()
        else:
            self.finish()

    def _pause(self):
        self.remaining_time -= self.table.calendar.time - self.deployment_time
        self.event.cancel()


class TimerCalendar(TimerTable):
    """An implementation of TimerTable that works with a Calendar object from utils.scheduling.
    Its timers correspond to events in the scheduling context. Repeating timers schedule a new
    event every time they are executed, hence creating an infinite chain of events. Non-repeating
    timers simply remove themselves from the timer table when they are executed."""
    def __init__(self, calendar=None):
        TimerTable.__init__(self, TimerEvent)
        self.calendar = calendar if calendar is not None else Calendar()


def _test():
    t = TimerCalendar()
    def foo():
        print "time = %s" % t.calendar.time
    t.schedule_interval(foo, 1)
    t.calendar.advance_time(10)
    return t

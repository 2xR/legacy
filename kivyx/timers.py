from kivy.clock import Clock
from utils import timers


class KivyTimer(timers.Timer):
    def _start(self):
        schedule_fnc = Clock.schedule_interval if self.repeat else Clock.schedule_once
        schedule_fnc(self._exec, self.delay)

    def _exec(self, dt):
        self.callback()
        if not self.repeat:
            self.running = False
            self.finish()

    def _pause(self):
        Clock.unschedule(self._exec)


def TimerTable():
    return timers.TimerTable(KivyTimer)

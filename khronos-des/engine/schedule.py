from khronos.utils import Deque

class Schedule(object):
    def __init__(self):
        self.dates = Deque()
        self.instants = {}
        
    def clear(self):
        self.dates.clear()
        self.instants.clear()
        
    def insert(self, event, date, priority):
        try:
            instant = self.instants[date]
        except KeyError:
            instant = self.instants[date] = Deque([(priority, event)])
            self.dates.insort(date)
        else:
            instant.insort((priority, event))
        event.__instant = instant
        event.__priority = priority
        
    def remove(self, event):
        instant = event.__instant
        if len(instant) > 1:
            instant.outsort((event.__priority, event))
        else:
            instant.pop()
            
    def advance(self):
        while True:
            date = self.dates[0]
            instant = self.instants[date]
            if len(instant) > 0:
                return instant, date
            self.dates.popleft()
            self.instants.pop(date)
            
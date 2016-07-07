from contextlib import contextmanager
from khronos.utils import Deque, indent
from khronos.des import Request

class History(object):
    """A data structure meant to hold the history of an object (e.g. a lot) as a collection of 
    time intervals. Each interval has a name, and may have associated data and/or subintervals.""" 
    def __init__(self, time_fnc):
        self.time_fnc = time_fnc
        self.content = []
        self.stack = [self]
        
    def __str__(self):
        return "\n".join(str(block) for block in self.content)
        
    @contextmanager
    def interval(self, name, *data, **kwdata):
        new_interval = self.start_interval(name, *data, **kwdata)
        yield
        assert self.end_interval() is new_interval
        
    def start_interval(self, name, *data, **kwdata):
        interval = HistoryBlock(name, self.time_fnc(), data, kwdata)
        self.stack[-1].content.append(interval)
        self.stack.append(interval)
        return interval
        
    def end_interval(self):
        interval = self.stack.pop()
        interval.end = self.time_fnc()
        return interval
        
class HistoryBlock(object):
    """A HistoryBlock represents an interval in an object's History."""
    def __init__(self, name, start, data, kwdata):
        self.name = name
        self.start = start
        self.end = None
        self.data = data
        self.kwdata = kwdata
        self.content = []
        
    def __str__(self):
        data = ", ".join(str(item) for item in self.data)
        kwdata = ", ".join("%s=%s" % (key, value) for key, value in self.kwdata.iteritems())
        if len(data) > 0:
            if len(kwdata) > 0:
                data = ", ".join((data, kwdata))
        else:
            data = kwdata
        lines = ["[%s, %s] :: %s(%s)" % (self.start, self.end, self.name, data)] 
        lines.extend(indent(str(block)) for block in self.content)
        return "\n".join(lines)
        
    @property
    def length(self):
        return self.end - self.start if self.end is not None else None
        
class Buffer(Deque):
    """A buffer class with a blocking get() method."""
    def __init__(self, *args, **kwargs):
        Deque.__init__(self, *args, **kwargs)
        self._requests = []
        
    def append(self, lot):
        if len(self._requests) > 0:
            self._requests[0].succeed(lot)
        else:
            Deque.append(self, lot)
            
    def get(self):
        return BufferRequest(self)
        
    def _add_request(self, request):
        if len(self) > 0:
            request.succeed(self.popleft())
        else:
            self._requests.append(request)
            
    def _remove_request(self, request):
        self._requests.remove(request)
        
class BufferRequest(Request):
    """A custom Request primitive for the Buffer class."""
    def constructor(self, buffer):
        self.buffer = buffer
        
    def deploy(self):
        self.buffer._add_request(self)
        
    def retract(self):
        self.buffer._remove_request(self)

from khronos.des import Process, Request
from khronos.utils import Deque

class Resource(Process):
    def __init__(self, name=None, parent=None, members=(), capacity=1):
        Process.__init__(self, name, parent, members)
        self.__capacity = capacity
        self.__available = capacity
        self.__requests = Deque()
        
    def status(self):
        return "%d of %d available (%d requests)" % \
            (self.__available, self.__capacity, len(self.__requests))
             
    def reset(self):
        self.__available = self.__capacity
        self.__requests.clear()
        
    def acquire(self, qty=1):
        if not isinstance(qty, int):
            raise TypeError("integer argument required")
        if qty > self.__capacity:
            raise ValueError("resource capacity exceeded")
        req = Request(qty)
        req.configure(self.__insert, self.__requests.remove)
        return req
        
    def __insert(self, req):
        if self.__available >= req.data:
            self.__available -= req.data
            req.fulfill()
        else:
            self.__requests.append(req)
            
    def release(self, qty=1):
        if not isinstance(qty, int):
            raise TypeError("int argument required")
        if self.__available + qty > self.__capacity:
            raise ValueError("resource capacity exceeded")
        self.__available += qty
        fulfilled = []
        for req in self.__requests:
            qty = req.data
            if qty <= self.__available:
                self.__available -= qty
                fulfilled.append(req)
        for req in fulfilled:
            req.fulfill()
            
    def set_capacity(self, capacity):
        if capacity == self.__capacity:
            return
        if self.running:
            delta = capacity - self.__capacity
            if delta < 0 and self.__available + delta < 0:
                raise ValueError("unable to reduce capacity (insufficient availability)")
            self.__capacity = capacity
            if delta > 0:
                self.release(delta)
            else:
                self.__available += delta
        else:
            self.__capacity = capacity
            
    def get_capacity(self):
        return self.__capacity
        
    def get_available(self):
        return self.__available
        
    def queue_size(self):
        return len(self.__requests)
        

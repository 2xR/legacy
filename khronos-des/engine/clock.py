from time import sleep


class Clock(object):
    """This class implements the simulation clock. The main role of the clock is to keep track of 
    the simulation time, but this class also provides conversion of time to the closest multiple 
    of a given 'precision' value, and approximate real-time simulation capability using the 
    time.sleep() function.
    A Clock object has the following attributes:
        value - the current clock value (a floating point number).
        maximum - upper limit of the clock's value. When this value is reached the advance_to() 
            method will stop at t=maximum and will return False, indicating that the desired 
            advance was not completed due to the clock's limitation. If the limit is None, no 
            limit is applied, meaning that advance_to() will always return True.
        precision - the smallest interval that the clock can represent. If set to None, 
            conversion will not truncate dates. If precision is not None, dates are truncated 
            using this value. See convert()'s documentation for more detail and examples.
        scale - specifies how many seconds to elapse in real time for each time unit elapsed in 
            simulation. For instance, if the scale is 1.0, then for each simulation time unit one 
            real time second is elapsed. To disable real-time scaling, set the scale to None."""
    def __init__(self, precision=None, scale=None):
        self.value = 0.0
        self.maximum = None
        self.precision = precision
        self.scale = scale
        
    def limit(self, rel=None, abs=None):
        if rel is not None and abs is not None:
            self.maximum = min(self.value + rel, abs)
        elif rel is not None:
            self.maximum = self.value + rel
        elif abs is not None:
            self.maximum = abs
        else:
            self.maximum = None
            
    def convert(self, t):
        """Truncate a time value according to the clock's precision value. 'precision' should be 
        a positive floating point number or None. The precision specifies the smallest interval 
        that can be represented by the clock. Values are converted to the nearest multiple of the 
        'precision' value if it is not None. If 'precision' is None, values are not modified. 
        Examples:
            precision = 0.0001
                0.123456789 -> 0.1235
        NOTE: This method is defined for external use by the simulator. Its purpose is to convert 
        event dates to correct values according to the clock's precision before entering them in 
        the global event schedule."""
        if self.precision is None:
            return t
        return int(t / self.precision + 0.5) * self.precision
        
    def clear(self):
        self.value = 0.0
        self.maximum = None
        
    def get(self):
        return self.value
        
    def advance_to(self, t):
        if t < self.value:
            raise ValueError("invalid date on advance (smaller than current clock value)")
        if self.maximum is not None and t > self.maximum:
            self.__advance_delta(self.maximum - self.value)
            return False
        self.__advance_delta(t - self.value)
        return True
        
    def __advance_delta(self, delta):
        self.value += delta
        if self.scale is not None:
            sleep(delta * self.scale)
            
from sys import stdout
from khronos.utils import indentation, fit_line


class Stack(object):
    """Simulator action stack. This is used to maintain active actions (succeeded or failed). A 
    detailed event trace (useful for model debugging) can be produced by the Stack class by 
    setting 'trace' to True."""
    def __init__(self, trace=True, width=0, out=stdout):
        self.trace = trace
        self.trace_width = width
        self.trace_out = out
        self.active = []
        
    def clear(self):
        self.active = []
        
    def message(self, text):
        if self.trace:
            self.trace_out.write(text + "\n")
            
    def instant(self, t):
        if self.trace:
            self.trace_out.write("Time = %s\n" % (t,))
            
    def push(self, action, activation_type):
        self.active.append(action)
        if self.trace:
            ind = indentation(len(self.active) - 1)
            line = "    |%s| %s%s :: %s" % (activation_type, ind, action, action.owner)
            if self.trace_width > 0:
                line = fit_line(line, self.trace_width)
            self.trace_out.write(line + "\n")
            
    def pop(self):
        return self.active.pop()
        
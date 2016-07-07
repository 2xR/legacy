from sys import stdout, stderr

from utils.prettyrepr import prettify_class
from utils.misc import check_type


@prettify_class
class Logger(object):
    """
    Log manager to facilitate the management of multiple log streams. Each stream can write to
    a file of its own (or a common file object), allowing the application to produce various
    output files for different categories of log messages.
    """
    def __init__(self, enabled=True):
        self.info = LogStream("Info", out=stdout)
        self.debug = LogStream("Debug", out=stderr, enabled=False)
        self.warning = LogStream("Warning", out=stderr)
        self.error = LogStream("Error", out=stderr)
        self.default = self.info
        self.streams = {self.info, self.debug, self.warning, self.error}
        self.state_stack = []
        if not enabled:
            self.disable()

    def __info__(self):
        enabled = []
        disabled = []
        for stream in self.streams:
            if stream.enabled:
                enabled.append(stream.name)
            else:
                disabled.append(stream.name)
        return "enabled={}, disabled={}".format(enabled, disabled)

    def write(self, fmt, *args):
        """Write a message into the logger's default stream."""
        self.default.write(fmt, *args)

    def flush(self):
        for stream in self.streams:
            stream.flush()

    def redirect_to(self, outfile):
        for stream in self.streams:
            stream.redirect_to(outfile)

    __call__ = write

    @property
    def enabled(self):
        return any(stream.enabled for stream in self.streams)

    @enabled.setter
    def enabled(self, enabled):
        (self.enable if enabled else self.disable)()

    def enable(self, *streams):
        self._multistream_call("enable", streams or self.streams)

    def disable(self, *streams):
        self._multistream_call("disable", streams or self.streams)

    def toggle(self, *streams):
        self._multistream_call("toggle", streams or self.streams)

    def _multistream_call(self, method, streams):
        """Call 'method' (a string, should be the name of a log stream method) on each of the
        argument 'streams'."""
        for stream in streams:
            if isinstance(stream, basestring):
                stream = getattr(self, stream)
            check_type(stream, LogStream)
            bound_method = getattr(stream, method)
            bound_method()

    def set_enabled(self, **state):
        """Allows setting the state of multiple log streams in a single call.
        Example:
            log = Logger()
            log.set_enabled(debug=False, info=True, warning=False, error=True)
        If called without arguments, this is equivalent to enable()."""
        if len(state) == 0:
            self.enable()
        else:
            for name, enabled in state.iteritems():
                stream = getattr(self, name)
                check_type(stream, LogStream)
                stream.enabled = enabled

    def save_state(self):
        state = {stream: stream.enabled for stream in self.streams}
        self.state_stack.append(state)

    def revert_state(self):
        state = self.state_stack.pop()
        for stream, enabled in state.iteritems():
            stream.enabled = enabled


@prettify_class
class LogStream(object):
    """
    Class implementing a simple stream of log messages written to a file-like object (can even be
    another log stream).
    """
    def __init__(self, name, out=stdout, enabled=True):
        self.name = name
        self.out = out
        self.enabled = bool(enabled)

    def __info__(self):
        status = "enabled" if self.enabled else "disabled"
        return "{}, {}".format(self.name, status)

    def redirect_to(self, outfile):
        self.out = outfile

    def write(self, fmt, *args):
        if self.enabled:
            message = fmt if len(args) == 0 else fmt.format(*args)
            if message.endswith("\n"):
                line = "[ {} ] {}".format(self.name, message)
            else:
                line = "[ {} ] {}\n".format(self.name, message)
            self.out.write(line)

    __call__ = write

    def flush(self):
        self.out.flush()

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def toggle(self):
        self.enabled = not self.enabled


Logger.Stream = LogStream

from utils.parallel.logger import Logger
from utils.parallel.auxiliary import Request, Result
from utils.parallel.auxiliary import ANY, ALL, traceback_as_string


class Worker(Logger):
    __slots__ = ("input", "output", "running")

    def __init__(self, input, output, log_queue, autorun=True):
        Logger.__init__(self, log_queue)
        self.debug(str((input, output, log_queue, autorun)))
        if self.name in (ANY, ALL):
            raise NameError("invalid name -- {!r}".format(self.name))
        self.input = input
        self.output = output
        self.running = False
        if autorun:
            self.run()

    def run(self):
        self._initialize()
        self._mainloop()
        self._finalize()

    def _initialize(self):
        self.debug("Initializing")
        self.on_initialize()

    def _mainloop(self):
        self.debug("Mainloop")
        self.running = True
        while self.running:
            self.debug("Waiting for request")
            req = self.input.recv()
            self.debug("Handling %s", req)
            assert req.target in (self.name, ANY, ALL)
            if req.type == Request.STOP:
                self.running = False
            else:
                try:
                    value = self.on_request(req)
                except Exception as error:
                    value = error
                    value.traceback = traceback_as_string()
                result = Result(req.id, self.name, value)
                self.debug("Produced %s", result)
                self.output.send(result)
        self.debug("Stopped")

    def _finalize(self):
        self.debug("Finalizing")
        self.on_finalize()
        self.input.close()
        self.output.close()
        self.debug("Finalized")

    def on_initialize(self):
        """OPTIONAL: Redefine in subclasses."""
        pass

    def on_request(self, req):
        """MANDATORY: Redefine in subclasses."""
        raise NotImplementedError()

    def on_finalize(self):
        """OPTIONAL: Redefine in subclasses."""
        pass

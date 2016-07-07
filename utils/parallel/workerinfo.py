from utils.prettyrepr import prettify_class


@prettify_class
class WorkerInfo(object):
    """Object bundling together all the information concerning a single worker that is relevant
    for a dispatcher.
    """
    __slots__ = ("name", "input", "output", "process", "local", "pending_results")

    def __init__(self, name, input, output, process=None):
        self.name = name
        self.input = input
        self.output = output
        self.process = process
        self.local = bool(process is not None)
        self.pending_results = 0

    def __info__(self):
        proc = ""
        if self.local:
            proc = "pid={}, ".format(self.process.pid)
        return "{} ({}pending_results={})".format(self.name, proc, self.pending_results)

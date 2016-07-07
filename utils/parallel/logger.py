import multiprocessing
import logging
import sys


class Logger(object):
    """An object which uses a logger object (from the standard library module 'logging') in a
    process-safe manner, i.e. without mixing up messages of different processes. This and other
    processes can log by placing messages in a log queue, and another process (the log process)
    has the role of busy items from the queue and printing the provided messages.
    """
    format = "[%(asctime)s | %(proc)s | %(levelname)s | %(name)s] %(message)s"
    __slots__ = ("name", "_log_queue", "_log_process")

    def __init__(self, log_queue=None):
        self.name = multiprocessing.current_process().name
        if log_queue is None:
            self._log_queue = multiprocessing.Queue()
            self._log_process = log_process(self._log_queue)
            self._log_process.start()
        else:
            self._log_queue = log_queue
            self._log_process = None

    def log(self, lvl, msg, *args):
        self._log_queue.put((self.name, lvl, msg, args))

    def debug(self, msg, *args):
        self._log_queue.put((self.name, logging.DEBUG, msg, args))

    def info(self, msg, *args):
        self._log_queue.put((self.name, logging.INFO, msg, args))

    def warn(self, msg, *args):
        self._log_queue.put((self.name, logging.WARNING, msg, args))

    def error(self, msg, *args):
        self._log_queue.put((self.name, logging.ERROR, msg, args))

    def critical(self, msg, *args):
        self._log_queue.put((self.name, logging.CRITICAL, msg, args))

    def shutdown(self):
        if self._log_process is not None and self._log_process.is_alive():
            self.debug("Shutting down logger...")
            self._log_queue.put(None)
            self._log_process.join()
            assert not self._log_process.is_alive()


def log_process(queue, name=__package__, level=logging.DEBUG):
    return multiprocessing.Process(name="log_process",
                                   target=_log_forever,
                                   args=(queue, name, level))


def _log_forever(queue, name, level):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(Logger.format))
    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(level)
    while True:
        obj = queue.get()
        if obj is None:
            break
        proc, lvl, msg, args = obj
        logger.log(lvl, msg, *args, extra={"proc": proc})

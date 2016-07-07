from multiprocessing import Process, Pipe, cpu_count
from Queue import Queue
from threading import Thread
from collections import deque

from utils.parallel.auxiliary import Request, Result, ANY, ALL
from utils.parallel.workerinfo import WorkerInfo
from utils.parallel.forwarder import Forwarder
from utils.parallel.logger import Logger
from utils.misc import check_type


class Dispatcher(Logger):
    NAME_SEP = "/"

    __slots__ = ("workers", "available", "requests", "results",
                 "pending_results", "messages", "forwarders", "running")

    def __init__(self, name=None):
        Logger.__init__(self)
        if name is not None:
            self.name = name
        if self.name in (ANY, ALL):
            raise NameError("invalid name -- {!r}".format(self.name))
        # Dispatcher-specific attributes
        # ------------------------------
        self.workers = {}         # {worker_name<str>: <WorkerInfo>}
        self.available = deque()  # [<WorkerInfo>] idle workers
        self.requests = deque()   # [<Request>] pending requests
        self.results = Queue()    # [<Result>] results buffer
        self.pending_results = 0  # <int> number of requests whose result is pending
        self.messages = Queue()   # [<Message>] pending messages (requests/results)
        self.forwarders = set()   # {<Forwarder>} message forwarders
        self.running = False      # <bool> running flag

    def add_worker(self, name, target, args=(), kwargs={}):
        worker_name = self.name + type(self).NAME_SEP + name
        if worker_name in self.workers:
            raise NameError("worker name already in use -- {!r}".format(worker_name))
        input_recv, input_send = Pipe(duplex=False)
        output_recv, output_send = Pipe(duplex=False)
        worker_proc = Process(name=worker_name,
                              target=target,
                              args=(input_recv, output_send, self._log_queue)+args,
                              kwargs=kwargs)
        worker_proc.start()
        input_recv.close()
        output_send.close()
        worker_info = WorkerInfo(worker_name, input_send, output_recv, worker_proc)
        self.workers[worker_name] = worker_info
        self.available.append(worker_info)
        self.forwarders.add(Forwarder(output_recv, self.messages, autorun=True))

    def add_workers(self, target, args=(), kwargs={}, count=0):
        """Create a number of identical worker processes (running the same callable with the same
        arguments)."""
        if count <= 0:
            count += cpu_count()
        for i in xrange(count):
            name = "{}#{}".format(target.__name__, i)
            self.add_worker(name, target, args, kwargs)

    # -------------------------------------------------------------------------
    # Run methods
    def run(self, separate_thread=False):
        if separate_thread:
            thread = Thread(target=self._run)
            thread.start()
            return thread
        else:
            self._run()

    def _run(self):
        self.debug("Running")
        self.running = True
        while self.running:
            self.step()
        self.debug("Stopped")
        self._finalize()

    def step(self, timeout=None):
        msg = self.messages.get(timeout=timeout)
        self.debug("Handling %s", msg)
        if isinstance(msg, Request):
            self._request(msg)
        elif isinstance(msg, Result):
            self._result(msg)
        else:
            raise ValueError("unexpected message received -- {}".format(msg))
        self.messages.task_done()

    def _finalize(self):
        self.debug("Finalizing...")
        # step() until all there are not unprocessed messages or pending results.
        while self.messages.qsize() > 0 or len(self.requests) > 0 or self.pending_results > 0:
            self.step()
        # Now we should be able to join() our message queue and message forwarders.
        self.messages.join()
        for forwarder in self.forwarders:
            forwarder.thread.join()
        # And join all worker processes.
        for worker_info in self.workers.itervalues():
            worker_info.input.close()
            worker_info.output.close()
            worker_info.process.join()
        # Finally we can shut down the log process and that should be everything.
        Logger.shutdown(self)

    def stop(self):
        """Put a STOP request in the dispatcher's message queue."""
        self.dispatch(Request.stop())

    def dispatch(self, req):
        """Put a Request in the dispatcher's message queue."""
        check_type(req, Request)
        self.messages.put(req)

    # -------------------------------------------------------------------------
    # Message handling
    def _request(self, req, force_processing=False):
        # If there are any requests in the request queue, those should
        # be processed first unless 'force_processing' is true.
        if not force_processing and len(self.requests) > 0:
            self.debug("Placing at the end of the queue %s", req)
            self.requests.append(req)
            return

        # Request must be sent to all workers (regardless of availability).
        if req.target == ALL:
            self.debug("Broadcasting %s", req)
            for worker_info in self.workers.itervalues():
                self.debug("\t-> %s", worker_info.name)
                self._send(req, worker_info)
            assert len(self.available) == 0
            # If this is a STOP request, the dispatcher's main loop is stopped.
            if req.type == Request.STOP:
                self.running = False

        # Request can be sent to any available worker.
        elif req.target == ANY:
            assert req.type != Request.STOP
            if len(self.available) > 0:
                self.debug("Dispatching %s to %s", req, self.available[0].name)
                self._send(req, self.available[0])
            else:
                self.debug("Queueing %s", req)
                self.requests.append(req)

        # Request was sent to a particular worker.
        else:
            assert req.type != Request.STOP
            self.debug("Forwarding %s", req)
            self._send(req, self.workers[req.target])

    def _send(self, req, worker_info):
        worker_info.input.send(req)
        if worker_info.pending_results == 0:
            self.available.remove(worker_info)
            self._log_available()
        if req.type != Request.STOP:
            worker_info.pending_results += 1
            self.pending_results += 1

    def _result(self, res):
        """Results are sent upstream or, if no upstream connection exists, stored in the results
        queue."""
        worker_info = self.workers[res.source]
        worker_info.pending_results -= 1
        self.pending_results -= 1
        assert worker_info.pending_results >= 0
        assert self.pending_results >= 0
        if worker_info.pending_results == 0:
            self.available.append(worker_info)
            self._log_available()
        self.results.put(res)

        # Try to process as many queued requests as possible.
        assert len(self.requests) == 0 or self.requests[0].target == ANY
        while len(self.requests) > 0:
            req = self.requests.popleft()
            if req.target == ANY:
                if len(self.available) > 0:
                    self._request(req, force_processing=True)
                else:
                    self.requests.appendleft(req)
                    break
            else:
                self._request(req, force_processing=True)
        assert len(self.requests) == 0 or self.requests[0].target == ANY

    def _log_available(self):
        """Print out the list of currently available workers."""
        self.debug("Available workers:\n\t" + "\n\t".join(map(str, self.available)))

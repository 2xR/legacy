from threading import Thread


class Forwarder(object):
    def __init__(self, source_conn, target_queue, autorun=True):
        self.source_conn = source_conn
        self.target_queue = target_queue
        self.running = False
        self.thread = None
        if autorun:
            self.run()

    def run(self):
        self.thread = Thread(target=self._run)
        self.thread.start()

    def _run(self):
        assert not self.running
        self.running = True
        while self.running:
            try:
                msg = self.source_conn.recv()
            except (IOError, EOFError):
                self.stop()
            else:
                self.target_queue.put(msg)

    def stop(self):
        self.running = False

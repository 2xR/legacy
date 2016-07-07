from utils.parallel import Worker, Dispatcher, Request
from Queue import Empty
from pprint import pprint
from time import sleep
import sys


class FooWorker(Worker):
    def on_initialize(self):
        self.global_data = ""

    def on_request(self, req):
        if req.type == "global data":
            self.global_data += req.data
            return None
        elif req.type == "sleep":
            sleep(req.data)
            return "slept for %s seconds" % (req.data,)
        elif req.type == "append":
            return self.global_data + req.data
        elif req.type == "prepend":
            return req.data + self.global_data
        elif req.type == "multiply":
            return self.global_data * req.data
        else:
            raise Exception("unknown request type -- {}".format(req.type))

reqs = [Request.broadcast("global data", "abra"),
        Request("append", "cadabra"),
        Request("prepend", "foobar"),
        Request("multiply", 3),
        Request("foo"),
        Request("sleep", 1, target="example1-local/FooWorker#1"),
        Request("sleep", 2),
        Request("sleep", 3),
        Request("sleep", 4),
        Request.stop()]


def consume_queue(Q):
    while True:
        try:
            yield Q.get_nowait()
        except Empty:
            break


def main_local():
    global reqs
    dispatcher = Dispatcher("example1-local")
    dispatcher.add_workers(FooWorker, count=4)
    thread = dispatcher.run(separate_thread=True)
    for req in reqs:
        dispatcher.dispatch(req)
    thread.join()
    pprint(list(consume_queue(dispatcher.results)))
    return dispatcher, thread


def main_server(address, authkey):
    global reqs
    dispatcher = Dispatcher("example1-client/server")
    dispatcher.add_workers(FooWorker, count=2)
    dispatcher.serve(address, authkey)
    dispatcher.run()


def main_client(address, authkey):
    global reqs
    dispatcher = Dispatcher("example1-client")
    dispatcher.add_remote("server", address, authkey)
    dsp_thread = dispatcher.run(separate_thread=True)
    for req in reqs:
        sleep(1)
        dispatcher.dispatch(req)
    dsp_thread.join()
    pprint(list(dispatcher.results))
    pprint(list(dispatcher.available))
    return dispatcher


if __name__ == "__main__":
    mode = "local" if len(sys.argv) == 1 else sys.argv[1]
    if mode == "local":
        main_local()
    else:
        ip = sys.argv[2]
        port = int(sys.argv[3])
        authkey = sys.argv[4]
        main = globals()["main_"+mode]
        main((ip, port), authkey)

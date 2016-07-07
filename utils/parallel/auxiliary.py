from StringIO import StringIO
import traceback
import sys

from utils.prettyrepr import prettify_class
from utils import text


ALL = "*"  # string used to target all workers
ANY = "?"  # string used to target any available worker


@prettify_class
class Message(object):
    REPR_MAXSIZE = 30

    __slots__ = ("type", "data")

    def __init__(self, type, data=None):
        self.type = type  # message type
        self.data = data  # data associated with the message

    def __info__(self):
        if self.data is None:
            data = ""
        else:
            data = " <{}>".format(text.fit(repr(self.data), type(self).REPR_MAXSIZE))
        return self.type + data


class Request(Message):
    STOP = "stop"
    next_id = 0

    __slots__ = ("id", "target")

    def __init__(self, type, data=None, target=ANY):
        Message.__init__(self, type, data)
        self.id = Request.next_id  # <int> *unique* request identifier
        self.target = target       # <str> target specifier (ANY, ALL, or worker)
        Request.next_id += 1

    def __info__(self):
        return "#{} {} to {}".format(self.id, Message.__info__(self), self.target)

    @classmethod
    def stop(cls):
        return cls(type=cls.STOP, target=ALL)

    @classmethod
    def broadcast(cls, type, data=None):
        """Creates a request whose targets are all workers."""
        return cls(type, data, target=ALL)


class Result(Message):

    __slots__ = ("id", "source")

    def __init__(self, id, source, data):
        Message.__init__(self, None, data)
        self.id = id          # <int> request id to which the result corresponds
        self.source = source  # <str> worker who produced the result

    def __info__(self):
        data = text.fit(repr(self.data), type(self).REPR_MAXSIZE)
        return "#{} <{}> by {}".format(self.id, data, self.source)


def traceback_as_string():
    """Return a string containing the traceback corresponding to the last exception."""
    buff = StringIO()
    _, _, tback = sys.exc_info()
    traceback.print_tb(tback, file=buff)
    return buff.getvalue()


# def send_msg(msg, conn, chunk_size=1024**2):
#     """This function can be used to send messages that are larger than the limit imposed by
#     multiprocessing. It works by breaking the message into chunks, sending the total size of
#     the message first, and then sending chunks one by one until the whole message is sent. The
#     other end of the connection should reconstruct the original message by putting together all
#     the chunks. The recv_msg() function does that, and is meant to be used together with this
#     function."""
#     size = len(msg)
#     start = 0
#     conn.send_bytes(str(size))
#     while start < size:
#         end = min(start+chunk_size, size)
#         conn.send_bytes(msg, start, end-start)
#         start = end


# def recv_msg(conn):
#     """Receive a message sent with send_msg()."""
#     size = int(conn.recv_bytes())
#     chunks = []
#     while size > 0:
#         chunk = conn.recv_bytes()
#         chunks.append(chunk)
#         size -= len(chunk)
#     if size < 0:
#         raise Exception("message size mismatching header size")
#     return "".join(chunks)

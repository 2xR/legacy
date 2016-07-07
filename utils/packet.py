from __future__ import absolute_import

from functools import partial
import cPickle as pickle
import socket
import threading
import zlib
import re

from utils.misc import check_type, ignored, consume


class Packet(object):
    """This class is responsible for the packing and unpacking of data. A packet consists of a
    simple fixed-length header containing the size (base 10 integer, in bytes) of the packet's
    payload, followed by the actual payload. The payload is nothing but the pickle dump (a string)
    of a given object. Use Packet.pack(obj) to create a packet from an object, or Packet.append()
    to accumulate the pickle of an object and then Packet.unpack() it."""
    HEADER_SIZE = 15
    HEADER_FORMAT = "<S{payload_size:010d}C{compressed:1d}>"
    HEADER_REGEX = re.compile("^<S(?P<payload_size>\d{10})C(?P<compressed>\d)>")

    __slots__ = ("header", "compressed", "payload_size", "payload")

    def __init__(self):
        self.header = ""
        self.compressed = None
        self.payload_size = None
        self.payload = None

    @classmethod
    def from_data(cls, data):
        packet = cls()
        packet.append(data)
        return packet

    def clear(self):
        self.header = ""
        self.compressed = None
        self.payload_size = None
        self.payload = None

    reset = clear

    def append(self, data):
        check_type(data, basestring)
        if self.payload_size is None:
            self.header += data
            self.parse_header()
        else:
            self.payload += data
        if self.payload_size is not None and len(self.payload) > self.payload_size:
            raise Exception("current payload size exceeds size declared in header")

    def parse_header(self):
        if self.payload_size is None and len(self.header) >= Packet.HEADER_SIZE:
            buff = self.header
            match = type(self).HEADER_REGEX.match(buff)
            self.compressed = bool(int(match.group("compressed")))
            self.payload_size = int(match.group("payload_size"))
            self.header = buff[:Packet.HEADER_SIZE]
            self.payload = buff[Packet.HEADER_SIZE:]

    @property
    def remaining(self):
        """Returns the number of bytes missing from the packet's payload, or, if the header is
        still incomplete (so we don't know the size of the payload), returns the number of bytes
        remaining in the header."""
        if self.payload_size is None:
            return Packet.HEADER_SIZE - len(self.header)
        else:
            return self.payload_size - len(self.payload)

    @property
    def is_empty(self):
        return len(self.header) == 0

    @property
    def is_complete(self):
        if self.payload_size is None:
            return False
        assert len(self.payload) <= self.payload_size
        return len(self.payload) == self.payload_size

    @classmethod
    def pack(cls, data, compress=False):
        payload = to_pickle(data)
        if compress:
            payload = zlib.compress(payload)
        packet = cls()
        packet.header = cls.HEADER_FORMAT.format(payload_size=len(payload), compressed=compress)
        packet.compressed = compress
        packet.payload_size = len(payload)
        packet.payload = payload
        return packet

    def unpack(self):
        if not self.is_complete:
            raise Exception("cannot unpack incomplete packet")
        pickled_data = self.payload if not self.compressed else zlib.decompress(self.payload)
        return from_pickle(pickled_data)


class PacketDispatcher(object):
    """This class uses a socket to communicate with other PacketDispatchers via TCP/IP (lan, wan,
    localhost, you name it :P). Sent data is wrapped with the Packet class, which adds a fixed-
    -length header to the data."""
    TIMEOUT = 1.0  # second

    __slots__ = ("socket", "packet", "running", "on_data_received")

    def __init__(self, socket, on_data_received=None):
        self.socket = socket                      # the socket used by the packet dispatcher
        self.socket.settimeout(self.TIMEOUT)      # make socket asynchronous
        self.packet = Packet()                    # used for accumulating messages
        self.running = False                      # running flag
        self.on_data_received = on_data_received  # callback run when a packet is complete

    def wait_for_data(self, separate_thread=False):
        if separate_thread:
            thread = threading.Thread(target=partial(consume, self._wait_for_data))
            thread.start()
        else:
            return self._wait_for_data()

    def _wait_for_data(self):
        if self.running:
            raise Exception("already waiting for data")
        self.running = True
        while self.running:
            while self.running and not self.packet.is_complete:
                with ignored(socket.timeout):
                    received = self.socket.recv(self.packet.remaining)
                    if len(received) == 0:  # connection closed from the other side
                        self.shutdown()
                        break
                    self.packet.append(received)
            if self.packet.is_complete:
                data = self.packet.unpack()
                self.packet.clear()
                if self.on_data_received is not None:
                    self.on_data_received(data)
                yield data
        if not self.packet.is_empty:
            raise Exception("incomplete packet remains unhandled")

    def stop(self):
        self.running = False

    def shutdown(self):
        self.stop()
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    def send(self, data, compress=False):
        packet = data if isinstance(data, Packet) else Packet.pack(data, compress=compress)
        self.socket.sendall(packet.header)
        self.socket.sendall(packet.payload)


Packet.Dispatcher = PacketDispatcher


def to_pickle(obj):
    """Creates a pickle from an object, calling __preserialize__() and __postserialize__() on the
    object if available. Data can be temporarily modified/removed from the object and returned by
    __preserialize__(). Any data returned by __preserialize__() will then be passed on to
    __postserialize__() so that the object's original state may be restored."""
    cls = type(obj)
    pre_serialize = getattr(cls, "__preserialize__", None)
    temp_data = None
    if callable(pre_serialize):
        temp_data = pre_serialize(obj)
    pickled_obj = pickle.dumps(obj)
    post_serialize = getattr(cls, "__postserialize__", None)
    if callable(post_serialize):
        post_serialize(obj, temp_data)
    return pickled_obj


def from_pickle(pickled_obj):
    """Opposite of to_pickle() (obviously). Calls __postdeserialize__() on the object if its class
    provides it and if it is a callable."""
    obj = pickle.loads(pickled_obj)
    cls = type(obj)
    post_deserialize = getattr(cls, "__postdeserialize__", None)
    if callable(post_deserialize):
        post_deserialize(obj)
    return obj

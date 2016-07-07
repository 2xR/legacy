from utils.prettyrepr import prettify_class


list_getitem = list.__getitem__

@prettify_class
class TaggableList(list):
    """
    A list whose positions (i.e. indices) can also be associated with arbitrary tags. Note that
    what is bound to keys are the indices, not the elements themselves, so if the contents of the
    list change, accessing tags will return the new values.

    A tag can be anything except an int, slice, list or tuple. These four types have a special
    meaning and actually address positions in the list.
    """
    __slots__ = ("address",)

    def __init__(self, iterable=None, tags=()):
        list.__init__(self)
        self.address = {}  # {tag: Address}
        if iterable is not None:
            self.extend(iterable, tags)

    def __info__(self):
        return "{}, tags={}".format(list.__repr__(self), self.address.keys())

    def __getitem__(self, addr):
        if isinstance(addr, (int, slice)):
            return list_getitem(self, addr)
        else:
            addr = Address.convert(addr)
            return [list_getitem(self, i) for i in addr.indices(self)]

    def append(self, obj, tags=()):
        list.append(self, obj)
        i = len(self) - 1
        for tag in tags:
            self.tag_append(tag, i)

    def extend(self, iterable, tags=()):
        n0 = len(self)
        list.extend(self, iterable)
        n1 = len(self)
        s = slice(n0, n1)
        for tag in tags:
            self.tag_append(tag, s)

    def clear(self):
        list.__delitem__(self, slice(None, None, None))
        self.address.clear()

    # -------------------------------------------------------------------------
    # Tag management methods
    def tags(self):
        return self.address.keys()

    def tags_iter(self):
        return self.address.iterkeys()

    def tag_clear(self, tag):
        del self.address[tag]

    def tag_set(self, tag, addr):
        addr = Address.convert(addr)
        self.address[tag] = addr
        return addr

    def tag_append(self, tag, addr):
        try:
            tag_addr = self.address[tag]
        except KeyError:
            tag_addr = self.address[tag] = Address.convert(addr)
        else:
            if isinstance(tag_addr, MultiAddress):
                tag_addr.append(addr)
            else:
                tag_addr = self.address[tag] = Address.new([tag_addr, addr])
        return tag_addr

    def tag_prepend(self, tag, addr):
        try:
            tag_addr = self.address[tag]
        except KeyError:
            tag_addr = self.address[tag] = Address.convert(addr)
        else:
            if isinstance(tag_addr, MultiAddress):
                tag_addr.prepend(addr)
            else:
                tag_addr = self.address[tag] = Address.new([addr, tag_addr])
        return tag_addr

    def tag_indices(self, tag):
        return self.address[tag].indices(self)


@prettify_class
class Address(object):
    __slots__ = ()

    def indices(self, sequence):
        """This method should return a (flat) iterable containing integer indices in 'sequence'."""
        raise NotImplementedError()


class IntAddress(int, Address):
    """
    A simple integer index. Nothing magical happening here ;)
    """
    __slots__ = ()

    def indices(self, sequence):
        return (self,)


class SliceAddress(Address):
    """
    A simple wrapper around the built-in 'slice' object (we cannot subclass 'slice' unfortunately).
    """
    __slots__ = ("slice",)

    def __init__(self, slice):
        self.slice = slice

    def __info__(self):
        return ":".join(map(repr, [self.slice.start, self.slice.stop, self.slice.step]))

    def indices(self, sequence):
        start, stop, step = self.slice.indices(len(sequence))
        return xrange(start, stop, step)


class MultiAddress(list, Address):
    __slots__ = ()
    __info__ = list.__repr__
    __repr__ = Address.__repr__
    __str__ = Address.__str__

    def include(self, addr):
        addr = Address.convert(addr)
        if isinstance(addr, MultiAddress):
            self.extend(addr)
        else:
            self.append(addr)

    def append(self, addr):
        list.append(self, Address.convert(addr))

    def prepend(self, addr):
        list.insert(self, 0, Address.convert(addr))

    def extend(self, addrs):
        list.extend(self, Address.convert(addrs))

    def indices(self, sequence):
        for addr in self:
            for i in addr.indices(sequence):
                yield i


class TagAddress(Address):
    """
    Requires that the target sequence has an 'address' attribute mapping tags to addresses.
    """
    __slots__ = ("tag",)

    def __init__(self, tag):
        self.tag = tag

    def __info__(self):
        return repr(self.tag)

    def indices(self, sequence):
        return sequence.address[self.tag].indices(sequence)


def address_new(x):
    if isinstance(x, int):
        return IntAddress(x)
    if isinstance(x, slice):
        return SliceAddress(x)
    if isinstance(x, (tuple, list)):
        return MultiAddress(Address.convert(y) for y in x)
    return TagAddress(x)


def address_convert(x):
    return x if isinstance(x, Address) else Address.new(x)


def address_add(a, b):
    r = MultiAddress()
    r.include(a)
    r.include(b)
    return r


def address_radd(a, b):
    r = MultiAddress()
    r.include(b)
    r.include(a)
    return r


Address.new = staticmethod(address_new)
Address.convert = staticmethod(address_convert)
Address.__add__ = address_add
Address.__radd__ = address_radd


def example():
    l = TaggableList("abcdefghijklmnopqrstuvwxyz")
    l.tag_set("vowels", map(l.index, "aeiou"))
    l.tag_set("foo", [slice(-5, None), "vowels", 14])
    print l["vowels"]
    print l["foo"]
    print l[-1, ::5, "vowels"]
    return l


if __name__ == "__main__":
    example()

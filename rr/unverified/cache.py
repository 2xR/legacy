from weakref import WeakKeyDictionary


def cached_property(fget, doc=None):
    """A property with lazy evaluation and caching. After a value has been computed and stored,
    accessing the property will simply retrieve the previously computed value.
        class Foo(object):
            @cached_property
            def bar(self):
                print "omg what a big computation i'm doing right now!"
                return 42  # the meaning of life, the universe, and everything

        baz = Foo()
        baz.bar  # will print "omg what a big computation i'm doing right now!"
        baz.bar  # will simply retrieve the value (and does NOT print the message)

    To invalidate the stored value and trigger a recomputation of the property, simply delete it
    with:
        del baz.bar
        baz.bar  # once again will print the message

    Notice of course that attempts to assign values to these properties will fail spectacularly ;)
    They're not supposed to be assigned values anyway.

    Another thing to note, and more important, is that the instances of the classes where these
    properties are used *MUST* be weak refereceable, since the property keeps the cache in a
    WeakKeyDictionary from the weakref module, with the (weak) keys being the objects themselves.
    This shouldn't be a problem however, since weak reference support is enabled by default on
    user-defined classes."""
    memo = WeakKeyDictionary()
    return property(fget=_cached_getter(fget, memo), fdel=_cached_deleter(memo), doc=doc)


def _cached_getter(fget, memo):
    def getter(obj):
        try:
            value = memo[obj]
        except KeyError:
            value = memo[obj] = fget(obj)
        return value
    getter.__name__ = fget.__name__
    getter.__doc__ = fget.__doc__
    return getter


def _cached_deleter(memo):
    def deleter(obj):
        memo.pop(obj, None)
    return deleter


def _test():
    class Foo(object):
        @cached_property
        def bar(self):
            print "omg what a big computation i'm doing right now!"
            return 42  # the meaning of life, the universe, and everything

    baz = Foo()
    baz.bar  # will print "omg what a big computation i'm doing right now!"
    baz.bar  # will simply retrieve the value (and does NOT print the message)

    del baz.bar
    baz.bar  # once again will print the message
    return baz

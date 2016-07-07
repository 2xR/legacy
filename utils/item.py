"""
Item getter, setter, and deleter function factories similar to the functions of the same name in
the utils.attr module.
"""


def getter(item):
    def item_getter(obj):
        return obj[item]
    item_getter.__name__ = "get[%s]" % (item,)
    return item_getter


def setter(item):
    def item_setter(obj, val):
        obj[item] = val
    item_setter.__name__ = "set[%s]" % (item,)
    return item_setter


def deleter(item):
    def item_deleter(obj):
        del obj[item]
    item_deleter.__name__ = "del[%s]" % (item,)
    return item_deleter

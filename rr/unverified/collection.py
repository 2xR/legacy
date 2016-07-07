from utils.prettyrepr import prettify_class


@prettify_class
class Collection(object):
    """
    A collection represents a set of objects associated with possibly multiple tags. Tags can be
    accessed in any order, and when a query results in a single-element set, the element itself is
    returned.
    """
    def __init__(self):
        self.all = set()  # {elems}
        self.elems = {}   # {tag: elems}
        self.tags = {}    # {elem: tags}

    def __info__(self):
        return "{} elems in {} tags".format(len(self.all), len(self.elems))

    @property
    def tagset(self):
        return self.elems.viewkeys()

    def clear(self):
        self.all.clear()
        self.elems.clear()
        self.tags.clear()

    def add(self, elem, *tags):
        if len(tags) == 0:
            raise Exception("at least one tag is required")
        for tag in tags:
            try:
                self.elems[tag].add(elem)
            except KeyError:
                self.elems[tag] = {elem}
        if elem in self.all:
            self.tags[elem].update(tags)
        else:
            self.tags[elem] = set(tags)
            self.all.add(elem)

    def remove(self, elem, *tags):
        elem_tags = self.tags[elem]
        if not elem_tags.issuperset(tags):
            error_tags = ", ".join(map(repr, set(tags) - elem_tags))
            raise ValueError("element does not have tags - {}".format(error_tags))
        if len(tags) == 0:
            tags = list(elem_tags)
        elem_tags.difference_update(tags)
        if len(elem_tags) == 0:
            del self.tags[elem]
            self.all.remove(elem)
        for tag in tags:
            tag_elems = self.elems[tag]
            tag_elems.remove(elem)
            if len(tag_elems) == 0:
                del self.elems[tag]

    def filter(self, *tags):
        if len(tags) == 0:
            raise Exception("at least one tag is required")
        unrecognized = set(tags).difference(self.elems.keys())
        if len(unrecognized) > 0:
            raise ValueError("unrecognized tags - {}".format(unrecognized))
        tags = iter(tags)
        result = set(self.elems[tags.next()])
        for tag in tags:
            result &= self.elems[tag]
        return result

    def __len__(self):
        return len(self.all)

    def __iter__(self):
        return iter(self.all)

    def __getitem__(self, key):
        return set(self.elems[key])

    def __and__(self, other):
        result = type(self)()
        if isinstance(other, Collection):
            for elem in self.all & other.all:
                tags = set(self.tags[elem])
                tags.intersection_update(other.tags[elem])
                if len(tags) > 0:
                    result.add(elem, *tags)
        else:
            for elem in self.elems[other]:
                result.add(elem, *self.tags[elem])
        return result

    def __or__(self, other):
        result = type(self)()
        if isinstance(other, Collection):
            for elem in self.all | other.all:
                tags = set(self.tags.get(elem, []))
                tags.update(other.tags.get(elem, []))
                result.add(elem, *tags)
        else:
            return NotImplemented
        return result

    def __sub__(self, other):
        result = type(self)()
        if isinstance(other, Collection):
            for elem in self.all:
                tags = set(self.tags[elem])
                tags.difference_update(other.tags.get(elem, []))
                if len(tags) > 0:
                    result.add(elem, *tags)
        else:
            if other not in self.elems:
                raise ValueError("unrecognized tag - {}".format(other))
            for elem, tags in self.tags.iteritems():
                if other not in tags:
                    result.add(elem, *tags)
        return result


# LOT_SIZING = "lot sizing"
# SCHEDULING = "scheduling"
# PARALLEL_MACHINES = "parallel machines"
# SINGLE_MACHINE = "single machine"
# CAPACITATED = "capacitated"
# COMPACT_FORMULATION = "compact formulation"
# EXTENDED_FORMULATION = "extended formulation"
#
#
# def example():
#     ls = Collection()
#     ls.add("foobar", LOT_SIZING, SCHEDULING, PARALLEL_MACHINES, COMPACT_FORMULATION)
#     ls.add("foo", LOT_SIZING, PARALLEL_MACHINES)
#     ls.add("bar", CAPACITATED, LOT_SIZING, SINGLE_MACHINE, EXTENDED_FORMULATION)
#     return ls

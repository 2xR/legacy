class MetaNodeBranches(object):
    """
    This simple object manages the unexpanded branches in a metanode.  The advance() method should
    be called after the creation of a child node.  This method returns True if there is a next
    branch, or False if there are no remaining branches.
    """
    __slots__ = ("metanode", "remaining", "next")

    def __init__(self, metanode):
        self.metanode = metanode
        self.remaining = None
        self.next = None

    def init(self):
        self.remaining = iter(self.metanode.node.branches())
        self.advance()

    def advance(self):
        try:
            self.next = self.remaining.next()
            return True
        except StopIteration:
            self.next = None
            self.remaining = None
            self.metanode.on_expansion_complete()
            return False

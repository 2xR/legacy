from collections import deque


class QuadTreeNode(object):
    def __init__(self, aabb, capacity=10, mergeable=True, parent=None):
        self.aabb = aabb
        self.objects = set()
        self.capacity = capacity
        self.mergeable = mergeable
        self.children = None
        self.parent = parent
        self.root = parent.root if parent is not None else self
        self.depth = (parent.depth + 1) if parent is not None else 0
        
    def __str__(self):
        contents = "inner node" if self.objects is None else self.objects
        return "%s(%s, %s)" % (type(self).__name__, self.aabb, contents)
        
    def __repr__(self):
        return "<%s @%08x>" % (str(self), id(self))
        
    def pprint(self, indent=0):
        print "%s%r" % ("  " * indent, self)
        if not self.is_leaf:
            for child in self.children:
                child.pprint(indent+1)
                
    @property
    def is_root(self):
        return self.parent is None
        
    @property
    def is_leaf(self):
        return self.children is None
        
    @property
    def object_count(self):
        return (len(self.objects) if self.is_leaf else 
                sum(node.object_count for node in self.children))
        
    # --------------------------------------------------------------------------
    # Add, remove, and move
    def add(self, obj):
        leaves = self.leaves_in(obj.aabb)
        for leaf in leaves:
            leaf._add(obj)
        return leaves
        
    def _add(self, obj):
        self.objects.add(obj)
        obj.leaves.add(self)
        self.split()
        
    def remove(self, obj):
        leaves = list(obj.leaves) if self.is_root else self.leaves_in(obj.aabb) 
        for leaf in leaves:
            leaf._remove(obj)
        return leaves
        
    def _remove(self, obj):
        self.objects.remove(obj)
        obj.leaves.remove(self)
        if self.parent is not None:
            self.parent.merge()
            
    def move(self, obj, dx=0.0, dy=0.0):
        if dx == 0.0 and dy == 0.0:
            return
        obj.aabb.move(dx, dy)
        if len(obj.leaves) == 1 and iter(obj.leaves).next().aabb.contains(obj.aabb):
            return
        self.root.remove(obj)
        self.root.add(obj)
        
##        candidates = deque(set(leaf.parent for leaf in obj.leaves))
##        visited = set(candidates)
##        self.root.remove(obj)
##        while len(candidates) > 0:
##            node = candidates.popleft()
##            node.add(obj)
##            if node.aabb.contains(obj.aabb):
##                break
##            if node.parent not in visited:
##                candidates.append(node.parent)
##                visited.add(node.parent)
                
    # --------------------------------------------------------------------------
    # Split and merge
    def split(self, force=False):
        assert self.is_leaf
        if not (force or len(self.objects) > self.capacity):
            return
        # create the four child nodes
        cls = type(self)
        self.children = tuple(cls(aabb, self.capacity, parent=self) for aabb in self.aabb.split())
        # and now we move all objects into the proper child nodes
        for obj in self.objects:
            obj.leaves.remove(self)
            self.add(obj)
        self.objects = None
        
    def merge(self, force=False):
        assert not self.is_leaf and all(child.is_leaf for child in self.children)
        if not ((force and self.object_count <= self.capacity) or 
                (self.mergeable and self.object_count <= self.capacity / 2)): 
            return
        # transfer all objects from child nodes (leaves) to this node
        self.objects = set()
        for child in self.children:
            self.objects.update(child.objects)
        # don't forget to update the leaf-set of each object accordingly
        for obj in self.objects:
            obj.leaves.difference_update(self.children)
            obj.leaves.add(self)
        self.children = None
        
    # --------------------------------------------------------------------------
    # Query methods
    def leaves_in(self, aabb):
        """Compute the list of leaf nodes that cover the area specified by 'aabb'."""
        leaves = []
        self._leaves_in(aabb, leaves)
        return leaves
        
    def _leaves_in(self, aabb, leaves):
        """Appends to list 'leaves' the leaf nodes that cover the area specified by 'aabb'. If the 
        node's aabb contains the argument aabb, the method returns True to signal the parent node 
        that the rest of its children can be skipped."""
        if self.aabb.intersects(aabb):
            if self.is_leaf:
                leaves.append(self)
            else:
                for child in self.children:
                    if child._leaves_in(aabb, leaves):
                        return True
            return self.aabb.contains(aabb)
        return False
        
    def objects_in(self, aabb):
        """Compute the set of objects whose aabb intersects with the argument aabb."""
        objects = set()
        for leaf in self.leaves_in(aabb):
            for obj in leaf.objects:
                if obj not in objects and aabb.intersects(obj.aabb):
                    objects.add(obj)
        return objects
        


class QuadTree(QuadTreeNode):
    pass
    
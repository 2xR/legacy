from geom2d.quadtree.tree import QuadTree


class QuadTreeObject(object):
    def __init__(self, aabb):
        self.aabb = aabb
        self.root = None
        self.leaves = set()
        
    def attach(self, root):
        assert self.root is None and root.is_root 
        root.add(self)
        self.root = root
        
    def detach(self):
        self.quadtree.remove(self)
        
    def move(self, dx=0.0, dy=0.0):
        self.quadtree.move(self, dx, dy)
            
    def collisions(self):
        """Compute the set of objects whose aabb intersects with this object's aabb."""
        objects = set([self])
        for leaf in self.leaves:
            for other_obj in leaf.objects:
                if other_obj not in objects and self.aabb.intersects(other_obj.aabb):
                    objects.add(other_obj)
        objects.remove(self)
        return objects
        
        
QuadTree.Object = QuadTreeObject

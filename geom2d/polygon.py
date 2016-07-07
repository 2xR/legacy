from geom2d.shape import Shape
from geom2d.segment import Segment


class Polygon(Shape):
    is_convex = True
    
    def vertices(self):
        raise NotImplementedError()
        
    def edges(self):
        vertices = tuple(self.vertices())
        for i in xrange(len(vertices)):
            j = (i + 1) % len(vertices)
            yield Segment(vertices[i], vertices[j])
            
    def segment_intersections(self, segment):
        """Segment intersections are rather easy to compute with polygons. A polygon must only 
        provide its list of vertices (adjacent vertices should be on adjacent positions in the 
        list), and a list of edges is automatically created from the vertices. Then, the segment 
        is intersected with each edge of the polygon, accumulating the intersection points.
        In case the polygon is convex, we can stop testing for intersections after we have two 
        points, since a line cannot intersect more than twice with any convex polygon."""
        points = []
        convex = self.is_convex
        for edge in self.edges():
            point = segment.intersection(edge)
            if point is not None:
                points.append(point)
                if convex and len(points) == 2:
                    break  # convex polygons cannot intersect a line more than twice
        return points
        
        

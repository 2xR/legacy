class Graph(object):
    """An undirected graph."""
    def __init__(self):
        self.vertices = set()
        self.edges = set()
        self.adjacent = {}

    def add_vertex(self, v):
        if v in self.vertices:
            raise Exception("duplicate attempt to add vertex to graph")
        self.vertices.add(v)
        self.adjacent[v] = set()

    def remove_vertex(self, v):
        for w in self.adjacent[v]:
            self.remove_edge(v, w)
        self.vertices.remove(v)
        self.adjacent.pop(v)

    def add_edge(self, v, w):
        if v not in self.vertices:
            self.add_vertex(v)
        if w not in self.vertices:
            self.add_vertex(w)
        self.edges.add(Graph.edge(v, w))
        self.adjacent[v].add(w)
        self.adjacent[w].add(v)

    def remove_edge(self, v, w):
        self.edges.remove(Graph.edge(v, w))
        self.adjacent[v].remove(w)
        self.adjacent[w].remove(v)

    @staticmethod
    def edge(v, w):
        return tuple(sorted([v, w]))

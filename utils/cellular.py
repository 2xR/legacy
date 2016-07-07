"""A simple module for cellular automata. Defines only boolean cells, but other types may be 
easily defined."""

import random


N, NE, E, SE, S, SW, W, NW = range(8)
DELTA_X = [0, +1, +1, +1, 0, -1, -1, -1]
DELTA_Y = [+1, +1, 0, -1, -1, -1, 0, +1]


class Cell(object):
    def __init__(self, automaton, x, y):
        self.automaton = automaton
        self.x = x
        self.y = y
        
    def __repr__(self):
        return "%s%s" % (type(self).__name__, self.coords)
        
    def __getitem__(self, direction):
        return self.automaton.neighbor(self, direction)
        
    @property
    def coords(self):
        return (self.x, self.y)
        
    def shuffle(self, rng=random):
        raise NotImplementedError()
        
    def step(self, rule=None):
        raise NotImplementedError()
        
    def update(self):
        raise NotImplementedError()
        
        
class BooleanCell(Cell):
    def __init__(self, automaton, x, y, value=False):
        Cell.__init__(self, automaton, x, y)
        self.value = value
        self.next = None
        
    def __repr__(self):
        return "%s%s" % (Cell.__repr__(self), "#" if self.value else ".")
        
    def __str__(self):
        return "#" if self.value else "."
        
    def shuffle(self, rng=random):
        assert self.next is None
        self.value = rng.choice([True, False])
        
    def step(self, rule=None):
        assert self.next is None
        if rule is None:
            rule = self.automaton.rule
        self.next = rule(self)
        
    def update(self):
        assert self.next is not None
        self.value = self.next
        self.next = None
        
        
class CellularAutomaton(object):
    def __init__(self, width, height, rule, cell_type=BooleanCell):
        self.grid = [[cell_type(self, x, y) for x in xrange(width)] for y in xrange(height)]
        self.rule = rule
        
    def __getitem__(self, (x, y)):
        return self.grid[y][x]
        
    def __str__(self):
        lines = []
        for row in self.grid:
            lines.append("".join(str(cell) for cell in row))
        return "\n".join(lines)
        
    def shuffle(self, rng=random):
        for row in self.grid:
            for cell in row:
                cell.shuffle(rng)
                
    def step(self):
        rule = self.rule
        for row in self.grid:
            for cell in row:
                cell.step(rule)
        for row in self.grid:
            for cell in row:
                cell.update()
                
    def neighbor_coords(self, cell, direction, distance=1):
        return self._fix_coords(cell.x + DELTA_X[direction] * distance,
                                cell.y + DELTA_Y[direction] * distance)
        
    def neighbor(self, cell, direction, distance=1):
        x, y = self.neighbor_coords(cell, direction, distance)
        return self.grid[y][x]
        
    def _fix_x(self, x):
        return x % self.width
    
    def _fix_y(self, y):
        return y % self.height
    
    def _fix_coords(self, x, y):
        return (self._fix_x(x), self._fix_y(y))
        
    @property
    def width(self):
        return len(self.grid[0])
        
    @property
    def height(self):
        return len(self.grid)
        
    
def bit(i):
    return 1 << i
    
    
def elementary_rule(n):
    def rule(cell):
        i = (int(cell[W].value) << 2) + (int(cell.value) << 1) + int(cell[E].value)
        return bool(n & bit(i))
    return rule
    
    
def test_automata():
    a = CellularAutomaton(99, 1, elementary_rule(150))
    a[a.width/2, 0].value = True
    print a
    for _ in xrange(100):
        a.step()
        print a
    return a
    
    
if __name__ == "__main__":
    test_automata()
    
from khronos.des import Process

class World(Process):
    """Represents a 2-dimensional space. This object keeps track of the positions of its clients,
    i.e. other processes in the simulation, and displays an animation of the simulation. 
    Optionally, it can simply record a 'video tape' of the simulation which can be later 
    visualized using a Display object."""
    
    
class Object2D(object):
    def __init__(self, x=0, y=0, heading=None, shape=None):
        self.x = x
        self.y = y
        self.heading = heading
        self.shape = shape
        
    def move(self, dx=0, dy=0):
        self.x += dx
        self.y += dy
        
    def move_to(self, x, y):
        self.x = x
        self.y = y
        
    def move_forward(self, n):
        self.x += cos(self.heading) * n
        self.y += sin(self.heading) * n
        
    def move_backward(self, n):
        self.x -= cos(self.heading) * n
        self.y -= sin(self.heading) * n
        
    def move_right(self, n):
        self.x += cos(self.heading - pi/2) * n
        self.y += sin(self.heading - pi/2) * n
        
    def move_left(self, n):
        self.x += cos(self.heading + pi/2) * n
        self.y += sin(self.heading + pi/2) * n
        
    def rotate(self, angle):
        self.heading = (self.heading + angle) % TWO_PI
        
    def rotate_to(self, target):
        self.heading = atan(float(target.y - self.y) / float(target.x - self.x))
        if target.x < self.x:
            self.heading += pi
            
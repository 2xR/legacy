"""
Ping-pong game example. This is an extremely simple simulation demonstrating action chains and 
signal-listener interaction.
"""

from khronos.des import Process, Simulator, Channel

class Pinger(Process):
    def initialize(self):
        while True:
            yield 1
            yield self.sim.channel.emit("ping")
            yield self.sim.channel.listen("pong")
            
class Ponger(Process):
    def initialize(self):
        while True:
            yield self.sim.channel.listen("ping")
            yield 1
            yield self.sim.channel.emit("pong")
            
sim = Simulator(name="ping-pong", members=[Pinger(name="pinger"), Ponger(name="ponger")])
sim.channel = Channel()
if __name__ == "__main__":
    sim.single_run(10)
    
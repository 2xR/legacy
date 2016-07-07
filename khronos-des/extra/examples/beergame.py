from khronos.des import Simulator, Process, Chain

class Player(Process):
    """A class for a participant of the beer game (retailer, wholesaler, distributor, or 
    manufacturer)."""
    initial_inventory = 12
    
    def reset(self):
        self.inventory = [self.initial_inventory]
        self.backlog = [0]
        self.cost = [0]
        
    def update(self, received, ordered):
        inventory = self.inventory[-1] + received
        backlog = self.backlog[-1] + ordered
        assert inventory > 0 or backlog >= 0
        shipped = min(inventory, backlog)
        inventory -= shipped
        backlog -= shipped
        self.inventory.append(inventory)
        self.backlog.append(backlog)
        if inventory > 0: cost.append(BeerGame.inventory_cost * inventory)
        else:             cost.append(BeerGame.backlog_cost * backlog)
        return shipped
        
    def order(self):
        return self.backlog[-1] + 4
        
class BeerGame(Simulator):
    inventory_cost = 0.5
    backlog_cost = 1.0
    demand = ([4] * 3) + ([8] * 47)
    production_delay = 0.25
    
    def reset(self):
        self.clear()
        self.chain = [Player(x) for x in "mdwr"]
        self.extend(self.chain)
        
    def initialize(self):
        orders = [elem.order() for elem in self.chain]
        orders.append(self.demand[0])
        while True:
            yield 1
            
            
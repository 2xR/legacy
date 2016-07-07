from khronos.utils import biased_choice
from components import Product, Order
import random
random.seed(0)

# ---------------------------------------------------------
# Parameters ----------------------------------------------
NPRODUCTS = 10          # Number of generated products
NORDERS = 100           # Number of generated orders
COMPLEXITY = (0.5, 2.0) # Product complexity bounds
CHANGEOVER = (0.0, 0.0) # Changeover time bounds
SETUP      = (1.0, 1.0) # Setup time bounds
QUANTITY = {5:   0.25,  # Quantity-probability map 
            10:  0.15, 
            20:  0.05, 
            40:  0.05, 
            80:  0.10, 
            160: 0.15, 
            320: 0.25}

# ---------------------------------------------------------
# Create the list of products -----------------------------
products = [Product("P%d" % (x,)) for x in xrange(NPRODUCTS)]
for product in products:
    for section in ("cut", "sew", "assy"):
        product.complexity[section] = random.uniform(*COMPLEXITY)
    product.complexity["bench"] = sum(product.complexity.values()) 
    
# ---------------------------------------------------------
# Create the list of orders -------------------------------
orders = [Order(x, quantity=biased_choice(QUANTITY.keys(), QUANTITY.values(), rng=random), 
                product=random.choice(products)) for x in xrange(NORDERS)]

# ---------------------------------------------------------
# Changeover times ----------------------------------------
changeover = dict(cut={}, sew={}, assy={})
for section in ("cut", "sew", "assy"):
    for prod0 in products:
        changeover[section][(None, prod0)] = random.uniform(*CHANGEOVER)
        for prod1 in products:
            if prod0 is not prod1:
                changeover[section][(prod0, prod1)] = random.uniform(*CHANGEOVER)
                
# ---------------------------------------------------------
# Setup times ---------------------------------------------
setup = dict(cut={}, sew={}, assy={})
for section in ("cut", "sew", "assy"):
    for product in products:
        setup[section][product] = random.uniform(*SETUP)
        
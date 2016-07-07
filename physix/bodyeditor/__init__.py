import os
import sys
from kivyx.resources import resource_add_path

this_dir = os.path.dirname(os.path.abspath(__file__))
resource_add_path(os.path.join(this_dir, "assets"), recursive=sys.maxint)

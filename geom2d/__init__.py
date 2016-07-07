from geom2d.geometry import Geometry
from geom2d.vector import Vector
from geom2d.segment import Segment
from geom2d.line import Line
from geom2d.ray import Ray

# from geom2d.shape import Shape
# from geom2d.circle import Circle
# from geom2d.polygon import Polygon
# from geom2d.rectangle import Rectangle
# from geom2d.aabb import AABB
# from geom2d.triangle import Triangle

# --------------------------------------------------------------------------------------------------
# Test functions
# from random import random


# def make_objs(nobjs=100):
#     objs = []
#     for x in xrange(nobjs):
#         x = random()
#         y = random()
#         w = random()
#         h = random()
#         objs.append(AABB((x, x+w), (y, y+h)))
#     return objs
    
    
# def pairwise_collisions(objs):
#     if not isinstance(objs, list):
#         objs = list(objs)
#     colls = [[] for i in xrange(len(objs))]
#     for i in xrange(len(objs)-1):
#         obj_i   = objs[i]
#         colls_i = colls[i]
#         for j in xrange(i+1, len(objs)):
#             obj_j   = objs[j]
#             colls_j = colls[j]
#             if obj_i.collides(obj_j):
#                 colls_i.append(obj_j)
#                 colls_j.append(obj_i)
#     return objs, colls
    
    

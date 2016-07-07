from kivy.vector import Vector
from utils.approx import Approx

# default relpoints
TOP = Vector(0.5, 1.0)
TOP_LEFT = Vector(0.0, 1.0)
TOP_RIGHT = Vector(1.0, 1.0)

BOTTOM = Vector(0.5, 0.0)
BOTTOM_LEFT = Vector(0.0, 0.0)
BOTTOM_RIGHT = Vector(1.0, 0.0)

CENTER = Vector(0.5, 0.5)
CENTER_LEFT = LEFT = Vector(0.0, 0.5)
CENTER_RIGHT = RIGHT = Vector(1.0, 0.5)


def relpoint_to_coords(widget, rel_point):
    """Compute the real coordinates of a relative point w.r.t. 'widget'."""
    return Vector(widget.x + rel_point[0] * widget.width,
                  widget.y + rel_point[1] * widget.height)


def coords_to_relpoint(widget, point):
    """Translate the given coordinates into a relative point w.r.t. 'widget'."""
    return Vector(float(point[0] - widget.x) / widget.width,
                  float(point[1] - widget.y) / widget.height)


def align_coords(widget, rel_point=CENTER, x=None, y=None):
    """A utility function for aligning a point in a widget with the given coordinates. Only the
    coordinates that are specified (x, y, or both) are changed."""
    x0, y0 = relpoint_to_coords(widget, rel_point)
    if x is not None:
        widget.x += x - x0
    if y is not None:
        widget.y += y - y0
    p = relpoint_to_coords(widget, rel_point)
    q = (x0 if x is None else x, y0 if y is None else y)
    assert Approx(0.0) == (p - q).length()


def align_widget(follower, align_by, followee, align_to=None):
    """Align a relpoint in a widget to a relpoint in another widget."""
    if align_to is None:
        align_to = align_by
    x, y = relpoint_to_coords(followee, align_to)
    align_coords(follower, align_by, x, y)


class AlignLink(object):
    """An AlignLink object keeps a relpoint (align_by) in one widget (follower) aligned with a
    relpoint (align_to) in another widget (followee) just like align_widget() does. However,
    instead of being one-shot like align_widget(), the alignment is also automatically updated
    when the second widget changes position or any of the two widgets changes size. Note that
    each AlignLink is responsible for aligning only one axis."""
    X_AXIS = "x"
    Y_AXIS = "y"
    AXES = (X_AXIS, Y_AXIS)

    # make default relpoints available through this class
    TOP = TOP
    TOP_LEFT = TOP_LEFT
    TOP_RIGHT = TOP_RIGHT
    BOTTOM = BOTTOM
    BOTTOM_LEFT = BOTTOM_LEFT
    BOTTOM_RIGHT = BOTTOM_RIGHT
    CENTER = CENTER
    CENTER_LEFT = LEFT = LEFT
    CENTER_RIGHT = RIGHT = RIGHT

    def __init__(self, axis, follower, align_by, followee, align_to=None):
        if axis not in AlignLink.AXES:
            raise ValueError("invalid axis - %s" % (axis,))
        if align_to is None:
            align_to = align_by
        link_attr = "__%s_alignlink" % axis
        if hasattr(follower, link_attr):
            raise Exception("widgets can only have one active %s align link" % (axis,))
        setattr(follower, link_attr, self)
        self.axis = axis
        self.follower = follower
        self.align_by = align_by
        self.followee = followee
        self.align_to = align_to
        follower.bind(size=self.update)
        followee.bind(size=self.update, pos=self.update)
        self.update()

    @classmethod
    def X(cls, follower, align_by, followee, align_to=None):
        return cls(cls.X_AXIS, follower, align_by, followee, align_to)

    @classmethod
    def Y(cls, follower, align_by, followee, align_to=None):
        return cls(cls.Y_AXIS, follower, align_by, followee, align_to)

    def __str__(self):
        return ("%s.%s(%s%08x%s -> %s%08x%s)" %
                (type(self).__name__, self.axis,
                 type(self.follower).__name__, id(self.follower), self.align_by,
                 type(self.followee).__name__, id(self.followee), self.align_to))

    def update(self, *args):
        x, y = relpoint_to_coords(self.followee, self.align_to)
        if self.axis is AlignLink.X_AXIS:
            align_coords(self.follower, self.align_by, x=x)
        else:
            align_coords(self.follower, self.align_by, y=y)

    def destroy(self):
        link_attr = "__%s_alignlink" % self.axis
        delattr(self.follower, link_attr)
        self.follower.unbind(size=self.update)
        self.followee.unbind(size=self.update, pos=self.update)

    @staticmethod
    def get(widget, axis):
        link_attr = "__%s_alignlink" % axis
        return getattr(widget, link_attr, None)

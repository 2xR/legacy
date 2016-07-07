from kivyx.links.align import AlignLink
from kivyx.links.size import SizeLink


class Link(object):
    """A wrapper around size link and align link. This object can be used to manage links even
    more conveniently than using separate objects for these tasks."""
    # provide references to the plain link classes
    Align = AlignLink
    Size = SizeLink
    # import dimension constants from SizeLink
    WIDTH = SizeLink.WIDTH
    HEIGHT = SizeLink.HEIGHT
    # import axis constants from AlignLink
    X_AXIS = AlignLink.X_AXIS
    Y_AXIS = AlignLink.Y_AXIS
    # import relpoint constants from AlignLink
    TOP = AlignLink.TOP
    TOP_LEFT = AlignLink.TOP_LEFT
    TOP_RIGHT = AlignLink.TOP_RIGHT
    BOTTOM = AlignLink.BOTTOM
    BOTTOM_LEFT = AlignLink.BOTTOM_LEFT
    BOTTOM_RIGHT = AlignLink.BOTTOM_RIGHT
    CENTER = AlignLink.CENTER
    CENTER_LEFT = LEFT = AlignLink.LEFT
    CENTER_RIGHT = RIGHT = AlignLink.RIGHT

    def __init__(self, widget,
                 align_x=None, align_y=None, align_xy=None,
                 width=None, height=None, size=None):
        """Operations supported by Link objects:
            Link(w1, align_xy=(CENTER, w2), width=(0.5, w3, HEIGHT), height=w4)

                or

            l = Link(w1)
            l.align_x = w2                  # align w1's center x to w2's center
            l.align_y = TOP, w2             # align w1's top y to w2's top
            l.align_y = TOP, w2, BOTTOM     # align w1's top y to w2's bottom
            l.align_xy = w2                 # align w1's center to w2's center
            l.align_xy = TOP_RIGHT, w2      # align w1's top-right to w2's top-right
            l.align_xy = CENTER, w2, TOP    # align w1' center to w2's top
            l.height = w2                   # make w1's height equal to w2's height
            l.width = 0.5, w2               # make w1's width half of w2's width
            l.width = 1.0, w2, HEIGHT       # make w1's width equal to w2's height
            l.size = w2                     # make w1's size equal to w2's size
            l.size = 0.8, w2                # make w1's size equal to 80% of w2's size
            l.size = (0.1, 0.2), w2         # make w1's width 10% of w2's width, and
                                            # its height equal to 20% of w2's height
        """
        if align_xy is not None and (align_x is not None or align_y is not None):
            raise ValueError("conflicting align commands")
        if size is not None and (width is not None or height is not None):
            raise ValueError("conflicting size commands")
        if hasattr(widget, "__link"):
            raise Exception("widgets can only have one associated link object")
        setattr(widget, "__link", self)  # store reference to prevent GC from claiming the Link
        self.widget = widget             # managed widget
        self._align_x = None             # AlignLink
        self._align_y = None             # AlignLink
        self._width = None               # SizeLink
        self._height = None              # SizeLink
        # initialize size and align links from arguments
        if size is not None:
            self.size = size
        else:
            if width is not None:
                self.width = width
            if height is not None:
                self.height = height
        if align_xy is not None:
            self.align_xy = align_xy
        else:
            if align_x is not None:
                self.align_x = align_x
            if align_y is not None:
                self.align_y = align_y

    def __str__(self):
        parts = ["%s{" % type(self).__name__]
        for link in (self._width, self._height, self._align_x, self._align_y):
            if link is not None:
                parts.append("\t%s" % link)
        parts.append("}")
        return "\n".join(parts)

    def update(self, *args):
        for link in (self._width, self._height, self._align_x, self._align_y):
            if link is not None:
                link.update()

    def destroy(self):
        for link in (self._width, self._height, self._align_x, self._align_y):
            if link is not None:
                link.destroy()
        self._width = None
        self._height = None
        self._align_x = None
        self._align_y = None
        delattr(self.widget, "__link")

    @staticmethod
    def get(widget):
        return getattr(widget, "__link", None)

    # -------------------------------------------------------------------------
    def align(self, axis, align_by, widget, align_to=None):
        if align_to is None:
            align_to = align_by
        a_link_attr = "_align_" + axis
        a_link = getattr(self, a_link_attr, None)
        if a_link is not None and a_link.followee is not widget:
            a_link.destroy()
            a_link = None

        if a_link is None:
            a_link = AlignLink(axis, self.widget, align_by, widget, align_to)
            setattr(self, a_link_attr, a_link)
        else:
            a_link.align_by = align_by
            a_link.align_to = align_to
            a_link.update()

    def no_align(self, axis):
        a_link_attr = "_align_" + axis
        a_link = getattr(self, a_link_attr, None)
        if a_link is not None:
            a_link.destroy()
            setattr(self, a_link_attr, None)

    # -------------------------------------------------------------------------
    def _get_align_link(self, axis):
        a_link_attr = "_align_" + axis
        a_link = getattr(self, a_link_attr, None)
        if a_link is None:
            return None
        return (a_link.align_by, a_link.followee, a_link.align_to)

    def _set_align_link(self, axis, value):
        align_by, widget, align_to = self._parse_alignlink(value)
        self.align(axis, align_by, widget, align_to)

    def _parse_alignlink(self, value):
        if not isinstance(value, (tuple, list)):
            widget = value
            align_by = align_to = Link.CENTER
        elif len(value) == 2:
            align_by, widget = value
            align_to = align_by
        elif len(value) == 3:
            align_by, widget, align_to = value
        else:
            raise ValueError("invalid align link spec - %s" % (value,))
        return (align_by, widget, align_to)

    def _del_align_link(self, axis):
        self.no_align(axis)

    # -------------------------------------------------------------------------
    @property
    def align_x(self):
        return self._get_align_link(Link.X_AXIS)

    @align_x.setter
    def align_x(self, value):
        self._set_align_link(Link.X_AXIS, value)

    @align_x.deleter
    def align_x(self):
        self._del_align_link(Link.X_AXIS)

    # -------------------------------------------------------------------------
    @property
    def align_y(self):
        return self._get_align_link(Link.Y_AXIS)

    @align_y.setter
    def align_y(self, value):
        self._set_align_link(Link.Y_AXIS, value)

    @align_y.deleter
    def align_y(self):
        self._del_align_link(Link.Y_AXIS)

    # -------------------------------------------------------------------------
    @property
    def align_xy(self):
        return (self.align_x, self.align_y)

    @align_xy.setter
    def align_xy(self, value):
        self.align_x = value
        self.align_y = value

    @align_xy.deleter
    def align_xy(self):
        del self.align_x
        del self.align_y

    # -------------------------------------------------------------------------
    @property
    def width(self):
        s_link = self._width
        return None if s_link is None else (s_link.ratio, s_link.followee, s_link.followee_dim)

    @width.setter
    def width(self, value):
        ratio, widget, dimension = self._parse_dimlink(value, Link.WIDTH)
        if self._width is not None and self._width.followee is not widget:
            self._width.destroy()
            self._width = None

        if self._width is None:
            self._width = SizeLink(self.widget, Link.WIDTH, widget, dimension, ratio)
        else:
            self._width.followee_dim = dimension
            self._width.ratio = ratio
            self._width.update()

    @width.deleter
    def width(self):
        if self._width is not None:
            self._width.destroy()
            self._width = None

    # -------------------------------------------------------------------------
    @property
    def height(self):
        s_link = self._height
        return None if s_link is None else (s_link.ratio, s_link.followee, s_link.followee_dim)

    @height.setter
    def height(self, value):
        ratio, widget, dimension = self._parse_dimlink(value, Link.HEIGHT)
        if self._height is not None and self._height.followee is not widget:
            self._height.destroy()
            self._height = None

        if self._height is None:
            self._height = SizeLink(self.widget, Link.HEIGHT, widget, dimension, ratio)
        else:
            self._height.followee_dim = dimension
            self._height.ratio = ratio
            self._height.update()

    @height.deleter
    def height(self):
        if self._height is not None:
            self._height.destroy()
            self._height = None

    # -------------------------------------------------------------------------
    def _parse_dimlink(self, value, default_dimension):
        if not isinstance(value, (tuple, list)):
            widget = value
            ratio = 1.0
            dimension = default_dimension
        elif len(value) == 2:
            ratio, widget = value
            dimension = default_dimension
        elif len(value) == 3:
            ratio, widget, dimension = value
        else:
            raise ValueError("invalid size link spec - %s" % (value,))
        return (ratio, widget, dimension)

    # -------------------------------------------------------------------------
    @property
    def size(self):
        return (self.width, self.height)

    @size.setter
    def size(self, value):
        width, height = self._parse_sizelink(value)
        self.width = width
        self.height = height

    @size.deleter
    def size(self):
        del self.width, self.height

    # -------------------------------------------------------------------------
    def _parse_sizelink(self, value):
        if not isinstance(value, (tuple, list)):
            widget = value
            width = (1.0, widget, Link.WIDTH)
            height = (1.0, widget, Link.HEIGHT)
        elif len(value) == 2:
            ratio, widget = value
            if isinstance(ratio, (tuple, list)):
                w, h = ratio
            else:
                w = h = ratio
            width = (w, widget)
            height = (h, widget)
        else:
            raise ValueError("invalid size spec - %s" % (value,))
        return (width, height)

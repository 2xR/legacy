from utils.approx import Approx


WIDTH = "width"
HEIGHT = "height"
DIMENSIONS = (WIDTH, HEIGHT)


class SizeLink(object):
    """Helper class for setting the width or height (follower_dim) of a widget (follower) relative
    to another widget's (followee) width or height (followee_dim).
    Do not use links on widgets whose parents are layouts that automatically try to resize them, as
    this will lead to unexpected results due to conflicts between the link and the layout."""
    WIDTH = WIDTH
    HEIGHT = HEIGHT

    def __init__(self, follower, follower_dim, followee, followee_dim=None, ratio=1.0):
        if follower_dim not in DIMENSIONS:
            raise ValueError("invalid follower dimension - %s" % (follower_dim,))
        if followee_dim is None:
            followee_dim = follower_dim
        elif followee_dim not in DIMENSIONS:
            raise ValueError("invalid followee dimension - %s" % (followee_dim,))
        link_attr = "__%s_sizelink" % follower_dim
        if hasattr(follower, link_attr):
            raise Exception("widgets can only have one active %s size link" % (follower_dim,))
        setattr(follower, link_attr, self)
        self.follower = follower
        self.follower_dim = follower_dim
        self.followee = followee
        self.followee_dim = followee_dim
        self.ratio = ratio
        followee.bind(**{followee_dim: self.update})
        self.update()

    def __str__(self):
        return ("%s(%s<%08x>.%s -> %s x %s<%08x>.%s)" %
                (type(self).__name__,
                 type(self.follower).__name__, id(self.follower), self.follower_dim, self.ratio,
                 type(self.followee).__name__, id(self.followee), self.followee_dim))

    def update(self, *args):
        reference = getattr(self.followee, self.followee_dim)
        setattr(self.follower, self.follower_dim, self.ratio * reference)
        assert getattr(self.follower, self.follower_dim) == Approx(self.ratio * reference)

    def destroy(self):
        link_attr = "__%s_sizelink" % self.follower_dim
        delattr(self.follower, link_attr)
        self.followee.unbind(size=self.update)

    @staticmethod
    def get(widget, dim):
        link_attr = "__%s_sizelink" % dim
        return getattr(widget, link_attr, None)

class TransformMode(object):
    """Base class for Mover, Rotator, and Extender."""
    def __init__(self):
        self.target = None

    def attach_to(self, widget):
        self.target = widget

    def detach(self):
        self.target = None

    def on_touch_down(self, touch):
        pass

    def on_touch_move(self, touch):
        pass

    def on_touch_up(self, touch):
        pass

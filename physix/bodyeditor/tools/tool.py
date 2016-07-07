class Tool(object):
    """A tool receives touch events from the editor's surface object. The tool's on_touch_XXX()
    methods should return a boolean indicating to the surface whether it should propagate that
    touch event to its children or not. The event is NOT propagated if True is returned, and it IS
    propagated if False is returned. This is the same as kivy's semantics for the return value of
    on_touch_XXX().
    """
    def __init__(self):
        # the toolbar does not allow changing tool while its current tool is in use
        self.in_use = False

    @property
    def button_text(self):
        return type(self).__name__

    def activate(self, editor):
        """Called by the toolbar when the tool is activated."""
        pass

    def deactivate(self, editor):
        """Called by the toolbar when the tool is deactivated."""
        pass

    def on_touch_down(self, touch):
        """Called by the surface when an 'on_touch_down' event is received. Should return True if
        the event is not to be propagated by the surface to its children, False otherwise."""
        return False

    def on_touch_move(self, touch):
        """Called by the surface when an 'on_touch_move' event is received. Should return True if
        the event is not to be propagated by the surface to its children, False otherwise."""
        return False

    def on_touch_up(self, touch):
        """Called by the surface when an 'on_touch_up' event is received. Should return True if
        the event is not to be propagated by the surface to its children, False otherwise."""
        return False

from utils.misc import check_type
from kivyx.misc import touch_to_local
from kivyx.widgets import Widget, ScatterPlane
from kivyx.links import Link

from physix.common import EditorObject
from physix.bodyeditor.objects import Origin


class Surface(Widget):
    """A surface is the drawing area of the editor, where magic stuff happens. Objects are drawn
    and removed from the surface with draw_object() and erase_object()."""
    INITIAL_SCALE = 100.0  # 1 unit of distance (i.e. a meter) is represented by 100 pixels

    def __init__(self, editor):
        Widget.__init__(self)
        self.editor = editor  # Editor
        self.plane = None     # ScatterPlane
        self.origin = None    # Origin (EditorObject)
        self.tool = None      # Tool
        self._build()

    def _build(self):
        self.plane = ScatterPlane()
        self.plane.do_translation = False
        self.plane.do_rotation = False
        self.plane.do_scale = False
        self.plane.scale = Surface.INITIAL_SCALE
        self.plane.bind(transform=self.update_plane_status)
        self.add_widget(self.plane)
        self.draw_origin()
        Link(self.plane, align_xy=(Link.BOTTOM_LEFT, self, Link.CENTER))

    def update_plane_status(self, *args):
        cx, cy = self.plane.to_local(*self.center)
        ox, oy = self.origin.pos
        msg = "Center=(%.2f,%.2f)  Scale=%.2f" % (cx - ox, cy - oy, self.plane.scale)
        self.editor.statusbar["coords"] = msg

    def set_pan_zoom_enabled(self, enabled):
        """Enable or disable pan/zoom on the surface."""
        self.plane.do_translation = bool(enabled)
        self.plane.do_scale = bool(enabled)

    def set_tool(self, tool, propagate=True):
        if self.tool is not None and self.tool.in_use:
            return
        if self.tool is not None:
            self.tool.deactivate(self.editor)
        self.tool = tool
        if tool is not None:
            self.tool.activate(self.editor)
        # keep surface and toolbar in sync
        if propagate:
            self.editor.toolbar.set_tool(tool, propagate=False)
        self.editor.statusbar["info"] = "Set tool to %s." % (tool.button_text,)

    def draw_origin(self):
        if self.origin is None:
            self.draw_object(Origin())

    def draw_object(self, widget):
        check_type(widget, EditorObject)
        if widget.id is None:
            widget.id = self.editor.id_generator(widget)
        if isinstance(widget, Origin):
            if self.origin is not None:
                raise ValueError("surface already has an origin")
            self.origin = widget
            self.origin.bind(pos=self.update_plane_status)
        self.plane.add_widget(widget)

    def erase_object(self, widget):
        self.plane.remove_widget(widget)
        if widget is self.origin:
            self.origin.unbind(pos=self.update_plane_status)
            self.origin = None

    def get_objects(self):
        return self.plane.children[:]

    def clear_objects(self):
        self.plane.clear_widgets()
        self.origin.unbind(pos=self.update_plane_status)
        self.origin = None

    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return False
        # add data to the touch: editor, surface, and convert the touch's coordinates to the
        # plane's coordinate system before passing the touch to the current tool
        touch.ud.editor = self.editor
        touch.ud.surface = self
        with touch_to_local(touch, self.plane):
            if self.tool is not None and self.tool.on_touch_down(touch):
                return True
        return Widget.on_touch_down(self, touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            with touch_to_local(touch, self.plane):
                if self.tool is not None and self.tool.on_touch_move(touch):
                    return True
            return Widget.on_touch_move(self, touch)
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            with touch_to_local(touch, self.plane):
                if self.tool is not None and self.tool.on_touch_up(touch):
                    return True
            return Widget.on_touch_up(self, touch)
        return False

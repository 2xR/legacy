from utils.misc import check_type

from kivyx.widgets import Widget, ScatterPlane
from kivyx.links import Link

from physix.common import EditorObject
from physix.worldeditor.objects import Origin


class Surface(Widget):
    """A surface is the drawing area of the editor, where magic stuff happens. Objects are drawn
    and removed from the surface with draw_object() and erase_object()."""
    INITIAL_SCALE = 100.0  # 1 unit of distance (i.e. a meter) is represented by 100 pixels

    def __init__(self, editor):
        Widget.__init__(self)
        self.editor = editor  # Editor
        self.plane = None     # ScatterPlane
        self.origin = None    # Origin (EditorObject)
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

    def draw_origin(self):
        if self.origin is None:
            self.draw_object(Origin())

    def draw_object(self, widget):
        check_type(widget, EditorObject)
        if isinstance(widget, Origin):
            if self.origin is not None:
                raise ValueError("surface already has an origin")
            self.origin = widget
            self.origin.bind(pos=self.update_plane_status)
        self.plane.add_widget(widget)

    def get_objects(self):
        return self.plane.children[:]

    def clear_objects(self):
        self.plane.clear_widgets()
        self.origin.unbind(pos=self.update_plane_status)
        self.origin = None


from math import pi, radians
from collections import Iterable

from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, NumericProperty, AliasProperty, ReferenceListProperty
from kivy.graphics import Color, Rectangle, Ellipse, InstructionGroup
from kivy.graphics import PushMatrix, PopMatrix, MatrixInstruction
from kivy.graphics.transformation import Matrix
from kivy.vector import Vector

from kivyx.misc import touch_to_local


class Transform(Widget):
    def __init__(self, **kwargs):
        self.__vx = 0.0  # x of the widget's viewport (bottom-left) in local coords
        self.__vy = 0.0  # y of the widget's viewport (bottom-left) in local coords
        self.__sx = 1.0  # x scale
        self.__sy = 1.0  # y scale
        self.__r = 0.0   # rotation (radians, not degrees kivy people!)
        self.__t = MatrixInstruction(self.transform_matrix)  # transform OpenGL instruction
        self.__dbg_origin = None     # debug graphics
        self.__dbg_viewport = None   # more debug graphics
        self.__dbg_aabb = None       # even more debug graphics :P
        self.touch_handlers = []     # non-widget objects which implement touch behavior
        Widget.__init__(self, **kwargs)
        self.canvas.before.add(PushMatrix())
        self.canvas.before.add(self.__t)
        self.canvas.after.add(PopMatrix())

    # -------------------------------------------------------------------------
    # Transform components (scale, rotation, translation), transform matrix and inverse
    scale_matrix = ObjectProperty(Matrix())
    rotation_matrix = ObjectProperty(Matrix())
    translation_matrix = ObjectProperty(Matrix())
    transform_matrix = ObjectProperty(Matrix())
    transform_inverse = ObjectProperty(Matrix())

    def __update_transform_matrix(self, instance, matrix):
        """Whenever any of the three transform components matrices (translation, rotation, scale)
        is modified, the transform matrix must be updated. This also updates the the OpenGL matrix
        instruction, and recomputes the transform inverse (used in to_local())."""
        t = self.translation_matrix
        r = self.rotation_matrix
        s = self.scale_matrix
        T = t.multiply(r).multiply(s)  # order of application s -> r -> t
        self.transform_matrix = T
        self.transform_inverse = T.inverse()
        self.__t.matrix = T

    on_translation_matrix = __update_transform_matrix
    on_rotation_matrix = __update_transform_matrix
    on_scale_matrix = __update_transform_matrix

    # -------------------------------------------------------------------------
    # do_translate(), do_translate_viewport(), do_scale(), and do_rotate()
    def do_translate(self, dx=0.0, dy=0.0):
        """Move the widget along with all its contents (i.e. this does not pan the viewport). If
        you want to change the view while maintaining the widget's position in its parent use
        do_translate_viewport() instead.
        NOTE: dx and dy are given in *PARENT* coordinates."""
        if dx == 0.0 and dy == 0.0:
            return False
        pox, poy = self.to_parent(0.0, 0.0)
        self.translation_matrix = Matrix().translate(pox + dx, poy + dy, 0.0)
        return True

    do_move = do_translate

    def do_translate_viewport(self, dx=0.0, dy=0.0):
        """Moves **the contents of the widget** while maintaining the widget in the same position.
        This is effectively the same as panning the view. To move the widget without panning the
        viewport use do_translate() instead.
        NOTE: dx and dy are given in *LOCAL* coordinates."""
        if dx == 0.0 and dy == 0.0:
            return False
        self.__vx += dx
        self.__vy += dy
        pdx, pdy = self.to_parent(dx, dy)
        pox, poy = self.to_parent(0.0, 0.0)
        self.do_translate(pox - pdx, poy - pdy)
        if dx != 0.0:
            Transform.viewport_x.trigger_change(self, None)
        if dy != 0.0:
            Transform.viewport_y.trigger_change(self, None)
        return True

    do_move_viewport = do_translate_viewport

    def do_scale(self, sx=1.0, sy=None, pivot=None):
        """Scale the contents of this widget by 'sx' and 'sy'. If only one value is provided, the
        scale is applied uniformly on both axes."""
        if sy is None:
            sy = sx
        if sx == 1.0 and sy == 1.0:
            return False
        if pivot is not None:
            self.do_translate_viewport(-pivot[0], -pivot[1])
        self.__sx *= sx
        self.__sy *= sy
        self.scale_matrix = Matrix().scale(self.__sx, self.__sy, 1.0)
        if sx != 1.0:
            Transform.scale_x.trigger_change(self, None)
        if sy != 1.0:
            Transform.scale_y.trigger_change(self, None)
        if pivot is not None:
            self.do_translate_viewport(+pivot[0], +pivot[1])
        return True

    def do_rotate(self, a=0.0, pivot=None):
        """Rotate the contents of the widget 'a' radians counterclockwise. Rotation always occurs
        around the origin of the widget's coordinate system."""
        if a == 0.0:
            return False
        if pivot is not None:
            self.do_translate_viewport(-pivot[0], -pivot[1])
        self.__r = (self.__r + a) % (2.0 * pi)
        self.rotation_matrix = Matrix().rotate(self.__r, 0, 0, 1)
        Transform.rotation.trigger_change(self, None)
        if pivot is not None:
            self.do_translate_viewport(+pivot[0], +pivot[1])
        return True

    # -------------------------------------------------------------------------
    # Coordinate system conversions (to_local(), to_parent(), collide_point())
    def align_local_to_parent(self, lx, ly, px, py):
        """Move the whole widget so that the local point (lx, ly) is aligned to the point (px, py)
        in parent coordinates."""
        px0, py0 = self.to_parent(lx, ly)
        self.do_translate(px - px0, py - py0)

    def to_parent(self, x, y, relative=False):
        """Convert coordinates from the widget's coordinate space to the parent's coordinate space.
        Here 'relative' is ignored because the argument coordinates are always relative to the
        origin of the widget's local coordinate space."""
        px, py, pz = self.transform_matrix.transform_point(x, y, 0)
        return (px, py)

    def to_local(self, x, y, relative=False):
        """Convert coordinates from the parent's coordinate space to the widget's coordinate space.
        Here 'relative' is ignored because the result is always relative to the origin of this
        widget's coordinate space."""
        lx, ly, lz = self.transform_inverse.transform_point(x, y, 0)
        return (lx, ly)

    def collide_point(self, x, y, local=False):
        """Return True if the point (x, y) collides with the widget's viewport. By default this
        function assumes the coordinates are given in parent coordinates and converts them to local
        coordinates before checking the collision. If 'local' is True, the conversion is skipped
        and the argument coordinates are check as-is."""
        if not local:
            x, y = self.to_local(x, y)
        vx = self.__vx
        vy = self.__vy
        return (vx <= x <= vx + self.viewport_width and
                vy <= y <= vy + self.viewport_height)

    # -------------------------------------------------------------------------
    # Default touch event handlers
    def on_touch_down(self, touch):
        # if not self.collide_point(touch.x, touch.y):
        #     return False
        with touch_to_local(touch, self):
            if Widget.on_touch_down(self, touch):
                return True
            if len(self.touch_handlers) > 0:
                for handler in self.touch_handlers:
                    if handler.on_touch_down(touch):
                        return True
        return False

    def on_touch_move(self, touch):
        # if not self.collide_point(touch.x, touch.y):
        #     return False
        with touch_to_local(touch, self):
            if Widget.on_touch_move(self, touch):
                return True
            if len(self.touch_handlers) > 0:
                for handler in self.touch_handlers:
                    if handler.on_touch_move(touch):
                        return True
        return False

    def on_touch_up(self, touch):
        # if not self.collide_point(touch.x, touch.y):
        #     return False
        with touch_to_local(touch, self):
            if Widget.on_touch_up(self, touch):
                return True
            if len(self.touch_handlers) > 0:
                for handler in self.touch_handlers:
                    if handler.on_touch_up(touch):
                        return True
        return False

    def add_touch_handler(self, ignore_oov=True):
        self.touch_handlers.append(TouchHandler(self, ignore_oov=ignore_oov))

    def clear_touch_handlers(self):
        del self.touch_handlers[:]

    # -------------------------------------------------------------------------
    # Widget position properties (in parent coords)
    def __parent_x_property(rel_x):
        def getter(self):
            (l, b), (r, t) = self.aabb
            return l + rel_x * (r - l)

        def setter(self, x):
            self.do_translate(x - getter(self), 0.0)
        return AliasProperty(getter, setter, bind=("aabb",))

    def __parent_y_property(rel_y):
        def getter(self):
            (l, b), (r, t) = self.aabb
            return b + rel_y * (t - b)

        def setter(self, y):
            self.do_translate(0.0, y - getter(self))
        return AliasProperty(getter, setter, bind=("aabb",))

    def __parent_pos_property(rel_x, rel_y):
        def getter(self):
            (l, b), (r, t) = self.aabb
            x = l + rel_x * (r - l)
            y = b + rel_y * (t - b)
            return (x, y)

        def setter(self, (x, y)):
            x0, y0 = getter(self)
            self.do_translate(x - x0, y - y0)
        return AliasProperty(getter, setter, bind=("aabb",))

    x = left = __parent_x_property(0.0)
    center_x = __parent_x_property(0.5)
    right = __parent_x_property(1.0)

    y = bottom = __parent_y_property(0.0)
    center_y = __parent_y_property(0.5)
    top = __parent_y_property(1.0)

    pos = bottom_left = __parent_pos_property(0.0, 0.0)
    center = __parent_pos_property(0.5, 0.5)
    top_right = __parent_pos_property(1.0, 1.0)

    # -------------------------------------------------------------------------
    # Viewport position properties (in local coords)
    def __viewport_x_property(rel_x):
        def getter(self):
            return self.__vx + rel_x * self.viewport_width

        def setter(self, x):
            self.do_translate_viewport(x - getter(self), 0.0)

        bind_props = () if rel_x == 0.0 else ("viewport_x", "viewport_width")
        return AliasProperty(getter, setter, bind=bind_props)

    def __viewport_y_property(rel_y):
        def getter(self):
            return self.__vy + rel_y * self.viewport_height

        def setter(self, y):
            self.do_translate_viewport(0.0, y - getter(self))

        bind_props = () if rel_y == 0.0 else ("viewport_y", "viewport_height")
        return AliasProperty(getter, setter, bind=bind_props)

    def __viewport_pos_property(rel_x, rel_y):
        def getter(self):
            x = self.__vx + rel_x * self.viewport_width
            y = self.__vy + rel_y * self.viewport_height
            return (x, y)

        def setter(self, (x, y)):
            x0, y0 = getter(self)
            self.do_translate_viewport(x - x0, y - y0)

        bind_props = ("viewport_x", "viewport_y")
        if rel_x != 0.0:
            bind_props += ("viewport_width",)
        if rel_y != 0.0:
            bind_props += ("viewport_height",)
        return AliasProperty(getter, setter, bind=bind_props)

    viewport_x = viewport_left = __viewport_x_property(0.0)
    viewport_center_x = __viewport_x_property(0.5)
    viewport_right = __viewport_x_property(1.0)

    viewport_y = viewport_bottom = __viewport_y_property(0.0)
    viewport_center_y = __viewport_y_property(0.5)
    viewport_top = __viewport_y_property(1.0)

    viewport_pos = viewport_bottom_left = __viewport_pos_property(0.0, 0.0)
    viewport_center = __viewport_pos_property(0.5, 0.5)
    viewport_top_right = __viewport_pos_property(1.0, 1.0)

    def __get_viewport_aabb(self):
        vx = self.__vx
        vy = self.__vy
        vw = self.viewport_width
        vh = self.viewport_height
        return (vx, vy), (vx+vw, vy+vh)

    def __set_viewport_aabb(self, (l, b), (r, t)):
        self.viewport_size = (abs(r - l), abs(t - b))
        self.viewport_pos = (min(l, r), min(b, t))

    viewport = viewport_aabb = AliasProperty(__get_viewport_aabb, __set_viewport_aabb,
                                             bind=("viewport_pos", "viewport_size"))

    # -------------------------------------------------------------------------
    # Viewport size properties (in local coords)
    viewport_width = NumericProperty(100.0)
    viewport_height = NumericProperty(100.0)
    viewport_size = ReferenceListProperty(viewport_width, viewport_height)

    # -------------------------------------------------------------------------
    # AABB size properties (in parent coords)
    def __get_width(self):
        (l, b), (r, t) = self.aabb
        return r - l

    def __set_width(self, w):
        ratio = float(w) / self.width
        if ratio != 1.0:
            pos0 = self.pos
            self.do_scale(ratio, ratio)
            self.pos = pos0

    def __get_height(self):
        (l, b), (r, t) = self.aabb
        return t - b

    def __set_height(self, h):
        ratio = float(h) / self.height
        if ratio != 1.0:
            pos0 = self.pos
            self.do_scale(ratio, ratio)
            self.pos = pos0

    def __get_size(self):
        (l, b), (r, t) = self.aabb
        return (r - l, t - b)

    def __set_size(self, (w, h)):
        w0, h0 = self.size
        w_ratio = float(w) / w0
        h_ratio = float(h) / h0
        ratio = min(w_ratio, h_ratio)
        if ratio != 1.0:
            pos0 = self.pos
            self.do_scale(ratio, ratio)
            self.pos = pos0

    width = AliasProperty(__get_width, __set_width, bind=("aabb",))
    height = AliasProperty(__get_height, __set_height, bind=("aabb",))
    size = AliasProperty(__get_size, __set_size, bind=("aabb",))

    # -------------------------------------------------------------------------
    # Scale properties: scale_x, scale_y, and scale (the latter can be assigned one or two values)
    def __get_scale_x(self):
        return self.__sx

    def __set_scale_x(self, sx):
        self.do_scale(sx / self.__sx, 1.0)

    def __get_scale_y(self):
        return self.__sy

    def __set_scale_y(self, sy):
        self.do_scale(1.0, sy / self.__sy)

    def __get_scale(self):
        return (self.__sx, self.__sy)

    def __set_scale(self, s):
        if isinstance(s, Iterable):
            sx, sy = s
        else:
            sx = sy = s
        self.do_scale(sx / self.__sx, sy / self.__sy)

    scale_x = AliasProperty(__get_scale_x, __set_scale_x)
    scale_y = AliasProperty(__get_scale_y, __set_scale_y)
    scale = AliasProperty(__get_scale, __set_scale, bind=("scale_x", "scale_y"))

    # -------------------------------------------------------------------------
    # Rotation (in radians)
    def __get_rotation(self):
        return self.__r

    def __set_rotation(self, a):
        self.do_rotate(a - self.__r)

    rotation = AliasProperty(__get_rotation, __set_rotation)

    # -------------------------------------------------------------------------
    # AABB (in parent coords, used by all the position properties, read-only)
    def __get_aabb(self):
        """Return the axis-aligned bounding box on the widget's viewport. This method returns a
        pair of points (left, bottom) and (right, top) in parent coordinates."""
        vx = self.__vx
        vy = self.__vy
        w = self.viewport_width
        h = self.viewport_height
        l, b = self.to_parent(vx, vy)
        r, t = l, b
        for lx, ly in ((vx+w, vy), (vx+w, vy+h), (vx, vy+h)):
            x, y = self.to_parent(lx, ly)
            if x < l:
                l = x
            elif x > r:
                r = x
            if y < b:
                b = y
            elif y > t:
                t = y
        return (l, b), (r, t)

    aabb = AliasProperty(__get_aabb, None, bind=("transform_matrix", "viewport_size"))

    # -------------------------------------------------------------------------
    # Debug properties
    def __debug_property(get_gfx, before=False, after=False, index=None):
        if before and after:
            raise ValueError("invalid arguments: both 'before' and 'after' are True")

        def target_instruction_group(self):
            if before:
                return self.canvas.before
            elif after:
                return self.canvas.after
            else:
                return self.canvas

        def add_gfx(self):
            gfx = get_gfx(self)
            target = target_instruction_group(self)
            if index is None:
                target.add(gfx)
            else:
                target.insert(index, gfx)

        def remove_gfx(self):
            gfx = get_gfx(self)
            target = target_instruction_group(self)
            target.remove(gfx)

        def getter(self):
            return get_gfx(self) in target_instruction_group(self).children

        def setter(self, enabled):
            was_enabled = getter(self)
            if enabled and not was_enabled:
                add_gfx(self)
            elif not enabled and was_enabled:
                remove_gfx(self)

        return AliasProperty(getter, setter)

    def __get_dbg_origin_gfx(self):
        if self.__dbg_origin is None:
            c1 = Color(1, 0, 0, 0.5)
            r1 = Rectangle()
            c2 = Color(0, 1, 0, 0.5)
            r2 = Rectangle()
            c3 = Color(0, 0, 1, 0.5)
            e = Ellipse()
            group = InstructionGroup()
            for instruction in (c1, r1, c2, r2, c3, e):
                group.add(instruction)

            def update_geom(_, (w, h)):
                r1.size = (w, 0.1 * h)
                r2.size = (0.1 * w, h)
                e.size = (0.5 * w, 0.5 * h)
                e.pos = (0.25 * w, 0.25 * h)

            self.bind(viewport_size=update_geom)
            update_geom(None, self.size)
            self.__dbg_origin = group
        return self.__dbg_origin

    def __get_dbg_viewport_gfx(self):
        if self.__dbg_viewport is None:
            c = Color(1, 1, 1, 0.5)
            r = Rectangle()
            group = InstructionGroup()
            for instruction in (c, r):
                group.add(instruction)

            def update_r(_, __):
                r.pos = self.viewport_pos
                r.size = self.viewport_size

            self.bind(viewport_pos=update_r, viewport_size=update_r)
            update_r(None, None)
            self.__dbg_viewport = group
        return self.__dbg_viewport

    def __get_dbg_aabb_gfx(self):
        if self.__dbg_aabb is None:
            c = Color(0.8, 0.8, 0.8, 0.3)
            r = Rectangle()
            group = InstructionGroup()
            for instruction in (c, r):
                group.add(instruction)

            def update_r(_, ((left, bottom), (right, top))):
                r.pos = (left, bottom)
                r.size = (right - left, top - bottom)

            self.bind(aabb=update_r)
            update_r(None, self.aabb)
            self.__dbg_aabb = group
        return self.__dbg_aabb

    debug_origin = __debug_property(__get_dbg_origin_gfx)
    debug_viewport = __debug_property(__get_dbg_viewport_gfx)
    debug_aabb = __debug_property(__get_dbg_aabb_gfx, before=True, index=0)

    # -------------------------------------------------------------------------
    # Global debug property
    def __get_dbg(self):
        return (self.debug_origin or
                self.debug_viewport or
                self.debug_aabb)

    def __set_dbg(self, enabled):
        self.debug_origin = enabled
        self.debug_viewport = enabled
        self.debug_aabb = enabled

    debug = AliasProperty(__get_dbg, __set_dbg,
                          bind=("debug_origin", "debug_viewport", "debug_aabb"))

    # -------------------------------------------------------------------------
    # Clean up the class's namespace
    del __update_transform_matrix
    del __parent_x_property
    del __parent_y_property
    del __parent_pos_property
    del __viewport_x_property
    del __viewport_y_property
    del __viewport_pos_property
    del __get_viewport_aabb
    del __set_viewport_aabb
    del __get_width
    del __set_width
    del __get_height
    del __set_height
    del __get_size
    del __set_size
    del __get_scale_x
    del __set_scale_x
    del __get_scale_y
    del __set_scale_y
    del __get_scale
    del __set_scale
    del __get_rotation
    del __set_rotation
    del __get_aabb
    del __debug_property
    del __get_dbg_origin_gfx
    del __get_dbg_viewport_gfx
    del __get_dbg_aabb_gfx
    del __get_dbg
    del __set_dbg


class TouchHandler(object):
    def __init__(self, transform, ignore_oov=True):
        self.ignore_oov = ignore_oov  # ignore out-of-viewport touches
        self.transform = transform
        self.touches = []
        self.prev_pos = {}
        self.do_translation = True
        self.do_rotation = True
        self.do_scale = True

    def on_touch_down(self, touch):
        if self.ignore_oov and not self.transform.collide_point(touch.x, touch.y, local=True):
            return
        touch.grab(self.transform)
        self.touches.append(touch)
        self.prev_pos[touch] = Vector(self.transform.to_parent(*touch.pos))

    def on_touch_move(self, touch):
        if touch.grab_current is not self.transform:
            return
        touch_point_in_parent = self.transform.to_parent(*touch.pos)

        if len(self.touches) == 1 and self.do_translation:
            ptx, pty = self.transform.pos
            px0, py0 = self.transform.to_parent(touch.px, touch.py)
            px1, py1 = touch_point_in_parent
            pdx, pdy = px1 - px0, py1 - py0
            self.transform.pos = ptx + pdx, pty + pdy
        else:
            touch_point = Vector(touch_point_in_parent)
            points = [self.prev_pos[t] for t in self.touches]
            pivot = max(points, key=touch_point.distance)
            farthest = max(points, key=pivot.distance)
            if points.index(farthest) == self.touches.index(touch):
                old_line = Vector(self.transform.to_parent(*touch.ppos)) - pivot
                new_line = Vector(touch_point_in_parent) - pivot

                vx, vy = self.transform.viewport_pos
                local_pivot = self.transform.to_local(*pivot)
                self.transform.viewport_pos = vx-local_pivot[0], vy-local_pivot[1]

                if self.do_rotation:
                    self.transform.do_rotate(radians(new_line.angle(old_line)))
                if self.do_scale:
                    ratio = new_line.length() / old_line.length()
                    self.transform.do_scale(ratio, ratio)
                self.transform.viewport_pos = vx, vy

        self.prev_pos[touch] = Vector(touch_point_in_parent)

    def on_touch_up(self, touch):
        if touch.grab_current is not self.transform:
            return
        touch.ungrab(self.transform)
        self.touches.remove(touch)
        del self.prev_pos[touch]


Transform.TouchHandler = TouchHandler

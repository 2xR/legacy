from contextlib import contextmanager
from functools import partial
import random
import wave

from kivy.graphics import Color, Rectangle
from kivy.uix.label import Label
from kivy.clock import Clock


@contextmanager
def touch_to_local(touch, widget):
    """Context manager. Inside a with block using this function, the touch's coordinates are
    converted from parent to local coordinates w.r.t. 'widget'. This is used in the on_touch_XXX()
    methods when propagating the touch to the widget's children.
    WARNING: using this on a touch whose coordinates have already been converted to local
    coordinates will lead to unexpected results."""
    touch.push()
    touch.apply_transform_2d(widget.to_local)
    yield
    touch.pop()


def iter_widget_tree(widget, level=0):
    """Iterator over the widget and its direct and indirect children. Yields (widget, level) pairs,
    where level is the distance between the widget and the root (the widget on which the function
    was first called)."""
    stack = [(widget, level)]
    while len(stack) > 0:
        widget, level = stack.pop()
        yield (widget, level)
        stack.extend((child, level+1) for child in widget.children)


def print_widget_tree(widget, level=0):
    for widget, level in iter_widget_tree(widget, level):
        rotation = ""
        if hasattr(widget, "rotation"):
            rotation = " (%.02f rad)" % widget.rotation
        print ("%s<%s center=[%.02f, %.02f] size=%s%s at %08X>" %
               ("  " * level, widget.__class__.__name__,
                widget.center_x, widget.center_y, widget.size, rotation, id(widget)))


def fps_label(update_interval=1.0, bbox_color=(0, 0, 0, .2), **kwargs):
    """Creates a label displaying the number of frames per second."""
    label = Label(**kwargs)
    label.bind(texture_size=label.setter("size"))
    show_bbox(label, color=bbox_color)

    def update(dt):
        label.text = "%.01f FPS" % Clock.get_fps()

    Clock.schedule_interval(update, update_interval)
    return label


def wav_length(wave_file):
    """Returns the length of a .wav file in seconds using Python's standard wave module (kivy's
    sound length is broken on Android)."""
    f = wave.open(wave_file, 'r')
    l = float(f.getnframes()) / f.getframerate()
    f.close()
    return l


def follow_props(follower, followee, *props):
    """Utility function to make 'follower's properties 'props' take the values of the properties
    with the same name on 'followee'."""
    bindings = {prop: follower.setter(prop) for prop in props}
    followee.bind(**bindings)


def update_texture_on_load(proxy_image, target):
    """This sets up an automatic update of a target widget's 'texture' when the image on a
    ProxyImage is loaded by the async image loader."""
    if not proxy_image.loaded:
        def update_texture_on_target(proxy):
            target.texture = proxy.image.texture
        proxy_image.bind(on_load=update_texture_on_target)


def show_bbox(widget, color=None, mode="rgba", geometry=Rectangle, under=True,
              follow_pos=True, follow_size=True, init_pos=(0, 0), init_size=(100, 100)):
    """Draws a colored geometry instruction (default=Rectangle) with the widget's size and position.
    Makes it easy to debug the positioning of widgets by seeing where their limits are located.
    NOTE: the geometry instruction must have a 'pos' and 'size'."""
    instruction_group = widget.canvas.before if under else widget.canvas
    with instruction_group:
        if color is None:
            Color(random.random(), 1.0, 1.0, 0.5, mode="hsv")
        else:
            Color(*color, mode=mode)
        geom = geometry(pos=init_pos, size=init_size)
        bind_geometry(geom, widget, pos=follow_pos, size=follow_size)
    return geom


def bind_geometry(geometry, widget, pos=True, size=True, pos_offset=None, size_offset=None):
    """Makes a geometry object's 'pos' and/or 'size' attributes follow 'widget's properties of the
    same name."""
    if pos:
        widget.bind(pos=partial(_geometry_set_pos, geometry, offset=pos_offset))
        _geometry_set_pos(geometry, widget, widget.pos, pos_offset)
    if size:
        widget.bind(size=partial(_geometry_set_size, geometry, offset=size_offset))
        _geometry_set_size(geometry, widget, widget.size, size_offset)


def _geometry_set_pos(geometry, widget, pos, offset):
    if offset is not None:
        pos = (pos[0] + offset[0], pos[1] + offset[1])
    geometry.pos = pos


def _geometry_set_size(geometry, widget, size, offset):
    if offset is not None:
        size = (size[0] + offset[0], size[1] + offset[1])
    geometry.size = size

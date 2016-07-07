import itertools

from physix.bodyeditor.tools import Tool
from physix.bodyeditor.tools.transform.mover import Mover
from physix.bodyeditor.tools.transform.extender import Extender
from physix.bodyeditor.tools.transform.rotator import Rotator


class TransformTool(Tool):
    button_text = "Transform"

    def __init__(self):
        Tool.__init__(self)
        self.picked_widget = None
        self.mover = Mover()
        self.rotator = Rotator()
        self.extenders = []
        for axis, direction in itertools.product(Extender.AXES, Extender.DIRECTIONS):
            self.extenders.append(Extender(axis, direction))

    def set_transformer(self, touch, transformer):
        #transformer_type = type(transformer).__name__
        width, height = self.picked_widget.viewport_size
        msg = "Transforming object with %.2fx%.2f meters..." % (width, height)

        touch.ud.editor.statusbar["info"] = msg
        touch.ud.transformer = transformer
        touch.grab(touch.ud.surface)
        transformer.on_touch_down(touch)
        self.in_use = True

    def deactivate(self, editor):
        if self.picked_widget is not None:
            self.unpick()

    def on_touch_down(self, touch):
        if self.in_use:
            return True
        if self.picked_widget is not None:
            widget = self.picked_widget
            lx, ly = widget.to_local(*touch.pos)
            if widget.rotatable and self.rotator.collide_point(lx, ly):
                self.set_transformer(touch, self.rotator)
                return True
            if widget.resizable:
                for extender in self.extenders:
                    if extender.collide_point(lx, ly):
                        self.set_transformer(touch, extender)
                        return True
            if widget.movable and widget.collide_point(*touch.pos):
                self.set_transformer(touch, self.mover)
                return True
        # check if we're picking a new object
        for child in touch.ud.surface.get_objects():
            child_transformable = child.movable or child.rotatable or child.resizable
            if child_transformable and child.collide_point(*touch.pos):
                self.pick(child)
                if child.movable:
                    self.set_transformer(touch, self.mover)
                return True
        return True

    def on_touch_move(self, touch):
        touch.ud.transformer.on_touch_move(touch)

        width, height = self.picked_widget.viewport_size
        msg = "Transforming object with %.2fx%.2f meters..." % (width, height)

        touch.ud.editor.statusbar["info"] = msg
        return True

    def on_touch_up(self, touch):
        touch.ud.editor.statusbar["info"] = "Transformation cancelled."
        touch.ud.transformer.on_touch_up(touch)
        touch.ungrab(touch.ud.surface)
        self.in_use = False
        return True

    def pick(self, widget):
        if self.picked_widget is not widget:
            # unpick previous object if necessary
            if self.picked_widget is not None:
                self.unpick()
            # attach mover, rotator, and extenders to the newly picked object
            if widget.movable:
                self.mover.attach_to(widget)
            if widget.rotatable:
                self.rotator.attach_to(widget)
            if widget.resizable:
                for extender in self.extenders:
                    extender.attach_to(widget)
        # mark object as picked
        self.picked_widget = widget

    def unpick(self):
        widget = self.picked_widget
        if widget.movable:
            self.mover.detach()
        if widget.rotatable:
            self.rotator.detach()
        if widget.resizable:
            for extender in self.extenders:
                extender.detach()
        self.picked_widget = None

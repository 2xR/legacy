from collections import Iterable

from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.graphics import InstructionGroup, Rectangle
from kivy.graphics import StencilPush, StencilPop, StencilUse, StencilUnUse

from kivyx.misc import bind_geometry


class Stencil(Widget):
    draw_fnc = ObjectProperty()

    def __init__(self, **kwargs):
        Widget.__init__(self, **kwargs)
        self.__stencil = InstructionGroup()
        self.__draw()
        if self.draw_fnc is None:
            self.draw_fnc = self.default_draw_fnc

    def __draw(self):
        self.canvas.before.add(StencilPush())
        self.canvas.before.add(self.__stencil)
        self.canvas.before.add(StencilUse())
        self.canvas.after.add(StencilUnUse())
        self.canvas.after.add(StencilPop())

    def on_draw_fnc(self, instance, draw_fnc):
        stencil = self.__stencil
        stencil.clear()
        if draw_fnc is not None:
            gfx = draw_fnc()
            if isinstance(gfx, Iterable):
                for instruction in gfx:
                    stencil.add(instruction)
            else:
                stencil.add(gfx)

    def default_draw_fnc(self):
        rect = Rectangle(size=self.size, pos=self.pos)
        bind_geometry(rect, self, pos=True, size=True)
        return rect

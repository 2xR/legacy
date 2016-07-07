from physix.bodyeditor.tools.transform.mode import TransformMode
from physix.bodyeditor.edithistory import Move


class Mover(TransformMode):
    def on_touch_down(self, touch):
        self.initial_pos = self.target.pos

    def on_touch_move(self, touch):
        self.target.do_translate(touch.dx, touch.dy)

    def on_touch_up(self, touch):
        if self.target.pos != self.initial_pos:
            touch.ud.editor.history.append(Move(self.target, self.initial_pos, self.target.pos))

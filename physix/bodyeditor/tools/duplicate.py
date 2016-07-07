from physix.bodyeditor.tools import Tool
from physix.bodyeditor.edithistory import Duplicate


class DuplicateTool(Tool):
    button_text = "Duplicate"

    def __init__(self):
        Tool.__init__(self)
        self.grabbed_widget = None

    def on_touch_down(self, touch):
        if self.in_use:
            return False
        # check if touch is over an editor object
        for child in touch.ud.surface.get_objects():
            if child.clonable and child.collide_point(*touch.pos):
                self.grabbed_widget = child
                touch.grab(touch.ud.surface)
                self.in_use = True
                touch.ud.editor.statusbar["info"] = "Duplicating object..."
                break
        return True

    def on_touch_up(self, touch):
        if self.grabbed_widget.collide_point(*touch.pos):
            touch.ud.editor.history.append(Duplicate(self.grabbed_widget))
            touch.ud.editor.statusbar["info"] = "Object duplicated."
        else:
            touch.ud.editor.statusbar["info"] = "Duplication canceled."
        self.grabbed_widget = None
        touch.ungrab(touch.ud.surface)
        self.in_use = False
        return True

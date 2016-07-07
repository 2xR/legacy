from physix.bodyeditor.tools import Tool
from physix.bodyeditor.edithistory import Erase


class TrashTool(Tool):
    button_text = "Trash"

    def __init__(self):
        Tool.__init__(self)
        self.grabbed_widget = None

    def on_touch_down(self, touch):
        if self.in_use:
            return False
        # check if touch is over an editor object
        for child in touch.ud.surface.get_objects():
            if child.deletable and child.collide_point(*touch.pos):
                # mark object being grabbed
                self.grabbed_widget = child
                # grab touch
                touch.grab(touch.ud.surface)
                # set tool in use
                self.in_use = True
                touch.ud.editor.statusbar["info"] = "Deleting object..."
                break
        return True

    def on_touch_up(self, touch):
        if self.grabbed_widget.collide_point(*touch.pos):
            # remove the widget if we are still touching it
            touch.ud.editor.history.append(Erase(self.grabbed_widget))
            touch.ud.editor.statusbar["info"] = "Object deleted."
        else:
            touch.ud.editor.statusbar["info"] = "Object not deleted."
        # unmark object being grabbed
        self.grabbed_widget = None
        # ungrab touch
        touch.ungrab(touch.ud.surface)
        # set tool not in use
        self.in_use = False
        return True

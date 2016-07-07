from physix.bodyeditor.tools.tool import Tool
from physix.bodyeditor.edithistory import Draw


class GeometryTool(Tool):
    """Base class for CircleTool and RectangleTool."""
    def on_touch_down(self, touch):
        if not self.in_use:
            self.in_use = True
            touch.grab(touch.ud.surface)
            # initialize init_pos and curr_pos
            self.curr_pos = self.init_pos = touch.pos
            # create the widget and the add a draw command to the edit history
            self.widget = self.new_widget()
            editor = touch.ud.editor
            editor.history.append(Draw(self.widget))

            width, height = self.widget.viewport_size
            editor.statusbar["info"] = "Creating new object with %.2fx%.2f meters..." % (width,
                                                                                         height)
        return True

    def on_touch_move(self, touch):
        self.curr_pos = touch.pos
        self.update_widget(self.widget)

        width, height = self.widget.viewport_size
        touch.ud.editor.statusbar["info"] = "Creating new object with %.2fx%.2f meters..." % \
                                            (width, height)
        return True

    def on_touch_up(self, touch):
        touch.ungrab(touch.ud.surface)
        if not self.valid_widget(self.widget):
            touch.ud.editor.history.pop()
            touch.ud.editor.statusbar["info"] = "No object created."
        else:
            width, height = self.widget.viewport_size
            touch.ud.editor.statusbar["info"] = "New object created with %.2fx%.2f meters." % \
                                                (width, height)
        self.in_use = False
        self.widget = None
        return True

    def new_widget(self):
        raise NotImplementedError()

    def update_widget(self, widget):
        raise NotImplementedError()

    def valid_widget(self, widget):
        raise NotImplementedError()

from physix.bodyeditor.tools.tool import Tool


class PanZoomTool(Tool):
    button_text = "Pan / Zoom"

    def __init__(self):
        Tool.__init__(self)
        self.touch_count = 0

    def activate(self, editor):
        editor.surface.set_pan_zoom_enabled(True)

    def deactivate(self, editor):
        editor.surface.set_pan_zoom_enabled(False)

    def on_touch_down(self, touch):
        touch.grab(touch.ud.surface)
        self.touch_count += 1
        self.in_use = True
        return False

    def on_touch_up(self, touch):
        touch.ungrab(touch.ud.surface)
        self.touch_count -= 1
        if self.touch_count == 0:
            self.in_use = False
        return False

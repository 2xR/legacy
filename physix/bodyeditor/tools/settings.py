from physix.bodyeditor.tools.tool import Tool
from physix.common.settings import SettingsPopup


class SettingsTool(Tool):
    button_text = "Settings"

    def __init__(self):
        Tool.__init__(self)

    def on_touch_down(self, touch):
        if self.in_use:
            return False
        self.in_use = True
        touch.grab(touch.ud.surface)
        return False

    def on_touch_up(self, touch):
        # check if touch is over an editor object
        for child in touch.ud.surface.get_objects():
            if child.collide_point(*touch.pos):
                # open the editor popup
                SettingsPopup(child, touch.ud.editor).open()
                break
        self.in_use = False
        touch.ungrab(touch.ud.surface)
        return False

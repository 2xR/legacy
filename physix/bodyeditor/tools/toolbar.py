from kivyx.widgets import Widget, BoxLayout, Button, Rectangle
from kivyx.links import Link


class ToolBar(Widget):
    def __init__(self, editor):
        Widget.__init__(self)
        self.editor = editor        # Editor
        self.curr_tool = None       # Tool
        self.prev_tool = None       # Tool
        self.tool_to_button = {}    # {Tool: Button}
        self.tool_highlight = None  # Rectangle
        self._build()

    def _build(self):
        layout = BoxLayout(orientation="horizontal")
        Link(layout, size=self, align_xy=self)
        self.add_widget(layout)

        self.tool_highlight = Rectangle()
        self.tool_highlight.rgba = (0, 0, 1, 0.5)
        self.tool_highlight.link = Link(self.tool_highlight)

        for tool_name in TOOL_NAMES:
            tool = TOOL_MAP[tool_name]
            button = Button(text=tool.button_text)
            button.bind(on_release=self.on_button)
            button.tool = tool
            layout.add_widget(button)
            self.tool_to_button[tool] = button

    def on_button(self, button):
        self.set_tool(button.tool)

    def set_tool(self, tool, propagate=True):
        # do nothing if current tool is being used
        if self.curr_tool is not None and self.curr_tool.in_use:
            return
        # move tool highlight to the new tool
        if self.tool_highlight.parent is not None:
            self.tool_highlight.parent.remove_widget(self.tool_highlight)
        button = self.tool_to_button[tool]
        button.add_widget(self.tool_highlight)
        self.tool_highlight.link.align_xy = button
        self.tool_highlight.link.size = button
        # update prev_tool and curr_tool, and set the tool on the surface object
        self.prev_tool = self.curr_tool
        self.curr_tool = tool
        # keep surface and toolbar in sync
        if propagate:
            self.editor.surface.set_tool(tool, propagate=False)

    def set_previous_tool(self):
        self.set_tool(self.prev_tool)

    def set_default_tool(self):
        self.set_tool(TOOL_MAP[TOOL_MAP["default"]])


from physix.bodyeditor.tools import (CircleTool, RectangleTool, PanZoomTool, TransformTool,
                                     DuplicateTool, TrashTool, SettingsTool)

TOOL_NAMES = ["circle", "rectangle", "panzoom", "transform", "duplicate", "trash", "settings"]
TOOL_MAP = {"default": "panzoom",
            "circle": CircleTool(),
            "rectangle": RectangleTool(),
            "panzoom": PanZoomTool(),
            "transform": TransformTool(),
            "duplicate": DuplicateTool(),
            "trash": TrashTool(),
            "settings": SettingsTool()}

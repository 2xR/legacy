from random import random, uniform
from math import hypot, pi, sin, cos
from utils.prettyrepr import prettify_class


class EditHistoryError(Exception):
    pass


class EditHistory(list):
    """The edit history provides undo/redo functionality."""
    Error = EditHistoryError

    def __init__(self, editor):
        list.__init__(self)
        self.position = 0     # index immediately after the last command
        self.editor = editor  # reference to the Editor object

    def clear(self):
        del self[:]
        self.position = 0

    def append(self, command):
        if self.position < len(self):
            del self[self.position:]
        list.append(self, command)
        self.position = len(self)
        command.do(self.editor)

    def pop(self):
        del self[self.position:]
        command = list.pop(self)
        command.undo(self.editor)
        self.position -= 1
        return command

    def undo(self):
        if self.position == 0:
            raise EditHistoryError("Cannot undo: already at beginning of edit history.")
        self.position -= 1
        command = self[self.position]
        command.undo(self.editor)
        return command

    def redo(self):
        if self.position == len(self):
            raise EditHistoryError("Cannot redo: already at end of edit history.")
        command = self[self.position]
        self.position += 1
        command.do(self.editor)
        return command


@prettify_class
class EditCommand(object):
    """Base class for edit commands. Edit commands must implement do() and undo()."""
    def do(self, editor):
        editor.file_manager.register_change(+1)
        editor.statusbar["info"] = "%s done." % (self,)

    def undo(self, editor):
        editor.file_manager.register_change(-1)
        editor.statusbar["info"] = "%s undone." % (self,)


class Draw(EditCommand):
    def __init__(self, obj):
        self.object = obj

    def __info__(self):
        return type(self.object).__name__

    def do(self, editor):
        editor.surface.draw_object(self.object)
        EditCommand.do(self, editor)

    def undo(self, editor):
        editor.surface.erase_object(self.object)
        EditCommand.undo(self, editor)


class Erase(EditCommand):
    def __init__(self, obj):
        self.object = obj

    def __info__(self):
        return type(self.object).__name__

    def do(self, editor):
        editor.surface.erase_object(self.object)
        EditCommand.do(self, editor)

    def undo(self, editor):
        editor.surface.draw_object(self.object)
        EditCommand.undo(self, editor)


class Move(EditCommand):
    def __init__(self, obj, source, target, attr="pos"):
        self.object = obj
        self.source = source
        self.target = target
        self.attr = attr

    def __info__(self):
        return ("%s.%s, (%.2f, %.2f) => (%.2f, %.2f)" %
                (type(self.object).__name__, self.attr,
                 self.source[0], self.source[1],
                 self.target[0], self.target[1]))

    def do(self, editor):
        setattr(self.object, self.attr, self.target)
        EditCommand.do(self, editor)

    def undo(self, editor):
        setattr(self.object, self.attr, self.source)
        EditCommand.undo(self, editor)


class Resize(EditCommand):
    def __init__(self, obj, size0, pos0, size1, pos1):
        self.object = obj
        self.size0 = size0
        self.pos0 = pos0
        self.size1 = size1
        self.pos1 = pos1

    def __info__(self):
        return ("%s, (%.2f, %.2f) => (%.2f, %.2f)" %
                (type(self.object).__name__,
                 self.size0[0], self.size0[1],
                 self.size1[0], self.size1[1]))

    def do(self, editor):
        self.object.viewport_size = self.size1
        self.object.pos = self.pos1
        EditCommand.do(self, editor)

    def undo(self, editor):
        self.object.viewport_size = self.size0
        self.object.pos = self.pos0
        EditCommand.undo(self, editor)


class Rotate(EditCommand):
    def __init__(self, obj, rotation0, rotation1):
        self.object = obj
        self.rotation0 = rotation0
        self.rotation1 = rotation1

    def __info__(self):
        return "%s, %.2f) => %.2f" % (type(self.object).__name__, self.rotation0, self.rotation1)

    def do(self, editor):
        self.object.rotation = self.rotation1
        EditCommand.do(self, editor)

    def undo(self, editor):
        self.object.rotation = self.rotation0
        EditCommand.undo(self, editor)


class Duplicate(EditCommand):
    def __init__(self, obj):
        self.object = obj
        self.clone = obj.duplicate()
        distance = hypot(0.2 * obj.viewport_width, 0.2 * obj.viewport_height)
        alpha = uniform(0.0, 2.0 * pi)
        self.clone.x += distance * cos(alpha)
        self.clone.y += distance * sin(alpha)
        self.clone.h = random()

    def __info__(self):
        return type(self.object).__name__

    def do(self, editor):
        editor.surface.draw_object(self.clone)
        EditCommand.do(self, editor)

    def undo(self, editor):
        editor.surface.erase_object(self.clone)
        EditCommand.undo(self, editor)


class ChangeSettings(EditCommand):
    def __init__(self, obj, old_settings, new_settings, setters):
        if set(old_settings.iterkeys()) != set(new_settings.iterkeys()):
            raise ValueError("mismatching key sets in settings dictionaries")
        self.object = obj
        self.old_settings = old_settings
        self.new_settings = new_settings
        self.setters = setters

    def do(self, editor):
        for setting_name, value in self.new_settings.iteritems():
            self.setters[setting_name](self.object, setting_name, value)
        EditCommand.do(self, editor)

    def undo(self, editor):
        for setting_name, value in self.old_settings.iteritems():
            self.setters[setting_name](self.object, setting_name, value)
        EditCommand.undo(self, editor)

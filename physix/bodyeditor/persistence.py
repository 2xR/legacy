import json

from physix.common import EditorObject


class Persister(object):
    """A persister is responsible for saving/loading the contents of the editor to/from files.
    This class provides json encoding/decoding for data as a default. Other types of encoding,
    such as XML or pickle protocol version 0 (the text-based one, others are binary) can be easily
    implemented by subclassing this class and redefining encode() and decode()."""
    def __init__(self, editor):
        self.editor = editor

    def save(self, filepath):
        specs = [o.extract_spec() for o in self.editor.surface.get_objects()]
        encoded_specs = self.encode(specs)
        with open(filepath, "w") as outfile:
            outfile.write(encoded_specs)

    def load(self, filepath):
        with open(filepath, "r") as infile:
            encoded_specs = infile.read()
        obj_specs = self.decode(encoded_specs)
        for obj_spec in obj_specs:
            obj_type = obj_spec["type"]
            obj = EditorObject.registry[obj_type].from_spec(obj_spec)
            self.editor.surface.draw_object(obj)

    def encode(self, obj_specs):
        """encode(obj_specs) -> str"""
        return json.dumps(obj_specs, indent=4)

    def decode(self, encoded_data):
        """decode(encoded_data) -> [ObjectSpec]"""
        return json.loads(encoded_data)

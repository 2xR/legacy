from kivy.resources import resource_add_path as kivy_resource_add_path
from kivy.resources import resource_find

from utils.namespace import Namespace

import os
import sys


__all__ = ("resource_find", "resource_add_path", "ResourceManager")


RESOURCE_CATEGORIES = {".png": ["images"],
                       ".jpg": ["images"],
                       ".jpeg": ["images"],
                       ".bmp": ["images"],
                       ".mp3": ["sounds"],
                       ".wav": ["sounds"],
                       ".ogg": ["sounds"],
                       ".flac": ["sounds"],
                       ".json": ["definitions"],
                       ".txt": ["docs"]}

class ResourceManager(object):
    """
    A manager for game resources that splits the resources by categories.
    Resources can be accessed by their name in three ways:
        - by category/extension through instance.category.extension.resource_name
                e.g. instance.images.png.logo
        - by name through instance.all.resource_name
                e.g. instance.all.logo
        - by relative path to the file through instance.paths.path.to.the.resource_name
                e.g. instance.paths.assets.images.logo

    The return value is the absolute path to the resource file being sought.
    """
    def __init__(self, resources=None, raise_on_not_found=True):
        self.raise_on_not_found = raise_on_not_found
        if resources is None:
            self.__resources = Namespace()
            self.__resources.all = Namespace()
            self.__resources.paths = Namespace()
        else:
            self.__resources = resources

    def keys(self):
        return self.__resources.keys()

    def values(self):
        return self.__resources.values()

    def __getattr__(self, attr):
        if attr not in self.__resources:
            if self.raise_on_not_found:
                raise KeyError(attr)
            return None
        if isinstance(self.__resources[attr], Namespace):
            return ResourceManager(resources=self.__resources[attr],
                                   raise_on_not_found=self.raise_on_not_found)
        return self.__resources[attr]

    def add_path(self, directory, recursive=sys.maxint, add_to_kivy=True):
        # add resource path to kivy; this is the default behaviour
        if add_to_kivy:
            kivy_resource_add_path(directory)
        # add this path to our searchable paths and recursively traverse its children
        for entry in os.listdir(directory):
            fullpath = os.path.join(directory, entry)
            if os.path.isdir(fullpath):
                if recursive > 0:
                    self.add_path(fullpath, recursive=recursive - 1, add_to_kivy=add_to_kivy)
            elif os.path.isfile(fullpath):
                self.add_resource(fullpath)

    def add_resource(self, filepath):
        root, ext = os.path.splitext(filepath)
        if ext not in RESOURCE_CATEGORIES:
            return

        basename = os.path.basename(filepath).lower()
        resource_name = self.__cleanup_name(basename.replace(ext, ""))
        abspath = os.path.abspath(filepath)

        # add the filepath to category/extension
        categories = RESOURCE_CATEGORIES[ext]
        for category in categories:
            self.__add_namespace(self.__resources, category)
            self.__add_namespace(self.__resources[category], ext[1:])
            self.__add_namespace(self.__resources[category][ext[1:]], resource_name, value=abspath)

        # add the filepath to all
        self.__add_namespace(self.__resources.all, resource_name, value=abspath)

        # add the filepath to relative
        paths = []
        root, path = os.path.split(filepath)
        root, path = os.path.split(root)
        while len(root) > 0:
            paths.append(path)
            previous_root = root
            root, path = os.path.split(root)
            if root == previous_root:
                break
        last_ns = self.__resources.paths
        if len(paths) > 0:
            paths = paths[::-1]
            for part in paths:
                self.__add_namespace(last_ns, part)
                last_ns = last_ns[part]
            if last_ns != self.__resources.paths:
                self.__add_namespace(last_ns, resource_name, value=abspath)

    def __add_namespace(self, namespace, name, value=None):
        if value is None and name not in namespace:
            namespace[name] = Namespace()
        elif value is not None:
            if name in namespace:
                one = namespace[name]
                two = value
                raise ValueError("Name collision between %s and %s" % (one, two))
            namespace[name] = value

    def __cleanup_name(self, name):
        name = name.replace(" ","_")
        if name.startswith("_"):
            name = name[1:]
        if name[0].isdigit():
            name = "_" + name
        return name.lower()


if __name__ == "__main__":
    rm = ResourceManager()
    rm.add_path(".")
    print rm.sounds.ogg
    print rm.all.the_ballzfather


def resource_add_path(directory, recursive=sys.maxint):
    """A replacement for kivy.resources.resource_add_path(). This has an additional argument which
    allows paths to be added recursively. If recursive is a positive integer, paths are added
    recursively up to the given number of levels. If recursive is negative, all sub-directories
    are added to kivy's resource search path. If recursive is zero, this function simply adds the
    argument directory to kivy's resource search path list."""
    print "adding resource directory:", directory
    kivy_resource_add_path(directory)
    if recursive == 0:
        return
    for entry in os.listdir(directory):
        fullpath = os.path.join(directory, entry)
        if os.path.isdir(fullpath):
            resource_add_path(fullpath, recursive - 1)

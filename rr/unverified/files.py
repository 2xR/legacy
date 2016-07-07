"""File-related utility functions."""
import os
import re


B = 1
KB = 2**10 * B
MB = 2**10 * KB
GB = 2**10 * MB
TB = 2**10 * GB


def file_size(path):
    size = os.stat(path)[6]
    for unit, name in [(TB, "TB"), (GB, "GB"), (MB, "MB"), (KB, "KB"), (B, "B")]:
        n = float(size) / unit
        if n >= 1.0:
            return "%.02f %s" % (n, name)
    raise ValueError("hum... this was unexpected :'(")


def detailed_file_size(path):
    size = os.stat(path)[6]
    sizes = []
    for unit, name in [(TB, "TB"), (GB, "GB"), (MB, "MB"), (KB, "KB"), (B, "B")]:
        n = size / unit
        if n > 0:
            sizes.append("%d%s" % (n, name))
            size -= n * unit
    return " ".join(sizes)


def find_files(directory, filters=None, recursive=True):
    directory = os.path.abspath(directory)
    matches = []
    if recursive:
        for dpath, _, fnames in os.walk(directory):
            for fname in fnames:
                if apply_filters(fname, filters):
                    matches.append(os.path.join(dpath, fname))
    else:
        for fname in os.listdir(directory):
            fpath = os.path.join(directory, fname)
            if os.path.isfile(fpath) and apply_filters(fname, filters):
                matches.append(fpath)
    return matches


def apply_filters(filename, filters):
    if filters is None:
        return True
    for filter_fnc in filters:
        if filter_fnc(filename):
            return True
    return False


def suffix_filter(suffix):
    def filter_fnc(filename):
        return filename.endswith(suffix)
    return filter_fnc


def preffix_filter(preffix):
    def filter_fnc(filename):
        return filename.startswith(preffix)
    return filter_fnc


def re_filter(regex):
    regex = re.compile(regex)

    def filter_fnc(filename):
        return regex.search(filename) is not None
    return filter_fnc


def dump(data, ostream, mode="a", conversion=str):
    data = conversion(data)
    if isinstance(ostream, basestring):
        with open(ostream, mode) as ostream:
            ostream.write(data)
            ostream.write("\n")
    else:
        ostream.write(data)
        ostream.write("\n")

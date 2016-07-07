#!/usr/bin/python

doc = """
%(app)s - create a zip file containing all files specified by extension.

Usage:
    %(app)s [-q] [-o OUT] [-i SUFFIXES] [-m MODE] <dir>...
    %(app)s (-h | --help | --version)
    
Options:
    --version                          Show program version and exit
    -h, --help                         Print this help message and exit
    -q, --quiet                        Display less information
    -o OUT, --output=<out>             Select an output file name [default: src.zip]
    -i SUFFIXES, --include=<suffixes>  Suffixes included in the zip file [default: .py]
    -m MODE, --mode=<mode>             Zip file open mode (accepts "w" or "a") [default: w]
""" % dict(app=__file__)

import os
from docopt import docopt
from zipfile import ZipFile


def do_print(message):
    print message
    
    
def no_print(message):
    pass
    
    
def make_zip(options):
    log = no_print if options["--quiet"] else do_print
    log("Creating source zip file in %s ..." % options["--output"])
    log("Included file suffixes: %s" % " ".join(options["<suffixes>"]))
    zip = ZipFile(options["--output"], options["--mode"])
    for dir in options["<dir>"]:
        add_directory(dir, zip, options, log)
    zip.close()
    log("Source zip created successfully")
    
    
def add_directory(basedir, zip, options, log):
    basedir = os.path.abspath(basedir)
    baseparent = os.path.normpath(os.path.join(basedir, ".."))
    log("checking directory %s ..." % basedir)
    for dirname, dirnames, filenames in os.walk(basedir):
        for filename in filenames:
            if any(filename.endswith(suffix) for suffix in options["<suffixes>"]):
                filepath = os.path.join(dirname, filename)
                archpath = os.path.relpath(filepath, baseparent)
                log("    -> %s ..." % archpath)
                zip.write(filepath, archpath)
                
                
options = docopt(doc, version="0.1.0a")
options["<suffixes>"] = [suffix.strip() for suffix in options["--include"].split(",")]
print options
make_zip(options)

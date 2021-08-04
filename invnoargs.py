#!/usr/bin/env python3
"""
"""
__url__     = 'http://smemsh.net/src/devskel/'
__author__  = 'Scott Mcdermott <scott@smemsh.net>'
__license__ = 'GPL-2.0'

from sys import argv, stdin, stdout, stderr, exit
from os.path import basename,
from subprocess import check_output

from os import (
    environ,
    EX_OK as EXIT_SUCCESS,
    EX_SOFTWARE as EXIT_FAILURE
)

###

def err(*args, **kwargs):
    print(*args, file=stderr, **kwargs)

def bomb(*args):
    err(*args)
    exit(EXIT_FAILURE)

def exe(cmd):
    return check_output(cmd.split()).splitlines()

###

def main():

    if debug: breakpoint()

    try: subprogram = globals()[invname]
    except (KeyError, TypeError):
        bomb(f"unimplemented command '{invname}'")

    instcnt = subprogram()

###

if __name__ == "__main__":

    from sys import version_info as pyv
    if pyv.major < 3 or pyv.major == 3 and pyv.minor < 9:
        bomb("minimum python 3.9")

    invname = basename(argv[0])
    args = argv[1:]

    try:
        from bdb import BdbQuit
        if bool(environ['DEBUG']):
            from pprint import pprint as pp
            debug = True
            err('debug-mode-enabled')
        else:
            raise KeyError

    except KeyError:
        debug = False

    try: main()
    except BdbQuit: bomb("debug-stop")

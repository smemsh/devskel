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
    getenv,
    EX_OK as EXIT_SUCCESS,
    EX_SOFTWARE as EXIT_FAILURE
)

###

def err(*args, **kwargs):
    print(*args, file=stderr, **kwargs)

def bomb(*args):
    err(*args)
    exit(EXIT_FAILURE)

def dprint(*args, **kwargs):
    if not debug: return
    err('debug:', *args, **kwargs)

def dprintvar(name, vars):
    if not debug: return
    err(f"debug: {name}")
    pp(vars[name])

def exe(cmd):
    return check_output(cmd.split()).splitlines()

###

def main():

    if debug == 1: breakpoint()

    try: subprogram = globals()[invname]
    except (KeyError, TypeError):
        bomb(f"unimplemented command '{invname}'")

    instcnt = subprogram()

###

if __name__ == "__main__":

    from sys import hexversion
    if hexversion < 0x03090000:
        bomb("minimum python 3.9")

    from bdb import BdbQuit
    debug = int(getenv('DEBUG') or 0)
    if debug:
        from pprint import pp
        err('debug: enabled')

    invname = basename(argv[0])
    args = argv[1:]

    try: main()
    except BdbQuit: bomb("debug: stop")

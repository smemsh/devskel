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
    close as osclose
    EX_OK as EXIT_SUCCESS,
    EX_SOFTWARE as EXIT_FAILURE
)

###

def err(*args, **kwargs):
    print(*args, file=stderr, **kwargs)

def bomb(*args, **kwargs):
    err(*args, **kwargs)
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

    try: return subprogram()
    finally: # cpython bug 55589
        try: stdout.flush()
        finally:
            try: stdout.close()
            finally:
                try: stderr.flush()
                finally: stderr.close()

###

if __name__ == "__main__":

    from sys import hexversion
    if hexversion < 0x03090000:
        bomb("minimum python 3.9")

    # for filters, save stdin, pdb needs stdio fds itself
    if select([sys.stdin], [], [], None)[0]:
        inbuf = sys.stdin.read() # todo: problematic with large inputs
        os.close(sys.stdin.fileno()) # cpython bug 73582
        try: sys.stdin = open('/dev/tty')
        except: pass # no ctty, but then pdb would not be in use
    else:
        bomb("must supply input on stdin")

    from bdb import BdbQuit
    debug = int(getenv('DEBUG') or 0)
    if debug:
        from pprint import pp
        err('debug: enabled')

    invname = basename(argv[0])
    args = argv[1:]

    try: main()
    except BdbQuit: bomb("debug: stop")

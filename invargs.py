#!/usr/bin/env python3
"""
"""
__url__     = 'http://smemsh.net/src/utilpy/'
__author__  = 'Scott Mcdermott <scott@smemsh.net>'
__license__ = 'GPL-2.0'

import argparse

from sys import argv, stdin, stdout, stderr, exit
from subprocess import check_output

from termios import tcgetattr, tcsetattr, TCSADRAIN
from tty import setraw

from os.path import basename, dirname, isdir, exists
from os import (
    getenv,
    getcwd, chdir, makedirs,
    access, W_OK,
    EX_OK as EXIT_SUCCESS,
    EX_SOFTWARE as EXIT_FAILURE,
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

def process_args():

    global args

    def addflag(p, flagchar, longopt, help=None, /, **kwargs):
        options = list(("-%s --%s" % (flagchar, longopt)).split())
        p.add_argument(*options, action='store_true', help=help, **kwargs)

    def addarg(p, vname, vdesc, help=None, /, **kwargs):
        p.add_argument(vname, metavar=vdesc, help=help, **kwargs)

    def addargs(*args, **kwargs):
        addarg(*args, nargs='*', **kwargs)

    def getchar():
        fd = stdin.fileno()
        tattrs = tcgetattr(fd)
        setraw(fd)
        c = stdin.buffer.raw.read(1).decode(stdin.encoding)
        tcsetattr(fd, TCSADRAIN, tattrs)
        return c

    p = argparse.ArgumentParser(
        prog            = invname,
        description     = __doc__.strip(),
        allow_abbrev    = False,
        formatter_class = argparse.RawTextHelpFormatter,
    )
    addflag (p, 'n', 'test', dest='dryrun')
    addflag (p, 'q', 'quiet')
    addflag (p, 'f', 'force')
    addarg  (p, 'src', 'srcdir')
    addarg  (p, 'dest', 'destdir')

    args = p.parse_args(args)

    args.ask = True if not args.force else False

    if args.quiet and args.ask:
        bomb("quiet mode cannot be interactive")
    if args.dryrun and args.force:
        bomb("the force is not with you")

    src = args.src if args.src else getcwd()
    dst = args.dest if args.dest else getenv('HOME')
    for d in ['src', 'dst']: exec(f"{d} = {d}.rstrip('/')")

    if args.ask:
        action = 'test' if args.dryrun else 'do_something'
        print(f"{action} '{src}/ -> '{dst}/' (y/n)? ", end='')
        stdout.flush()
        yn = getchar(); print(yn)
        if yn != 'y': bomb('aborting')

    return abspath(src), abspath(dst)


def check_sanity(src, dst):

    if not isdir(src):
        bomb("source dir invalid")

    if not exists(dst):
        try: makedirs(dst)
        except: bomb(f"dest '{dst}' dne or bad mkdir")

    elif not isdir(dst):
        bomb(f"refusing overwrite of '{dst}' (not a directory)")

    if not access(dst, W_OK):
        bomb(f"cannot write to destdir '{dst}'")

###

def main():

    if debug == 1: breakpoint()

    src, dst = process_args()
    check_sanity(src, dst)

    try: chdir(src)
    except: bomb(f"cannot change directory to '{src}'")

    try: subprogram = globals()[invname]
    except (KeyError, TypeError):
        bomb(f"unimplemented command '{invname}'")

    return subprogram(src, dst)

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

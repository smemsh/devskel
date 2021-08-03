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
    getenv, environ,
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

def exe(cmd):
    return check_output(cmd.split()).splitlines()

###

def process_args():

    global args

    def addflag(p, flagchar, longopt, help=None, /, **kwargs):
        options = list(("-%s --%s" % (flagchar, longopt)).split())
        p.add_argument(*options, action='store_true', help=help, **kwargs)

    def addarg(p, vname, vdesc, help=None, /, **kwargs):
        p.add_argument(vname, nargs='?', metavar=vdesc, help=help, **kwargs)

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
    src = src[:-1] if src[-1] == '/' else src
    dst = dst[:-1] if dst[-1] == '/' else dst

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

    from sys import version_info as pyv
    if pyv.major < 3 or pyv.major == 3 and pyv.minor < 9:
        bomb("minimum python 3.9")

    invname = basename(argv[0])
    args = argv[1:]

    try:
        if bool(environ['DEBUG']):
            from pprint import pprint as pp
            debug = True
            err('debug-mode-enabled')
        else:
            raise KeyError

    except KeyError:
        debug = False

    if debug: breakpoint()

    main()

#!/usr/bin/env python3
"""
"""
__url__     = 'http://smemsh.net/src/devskel/'
__author__  = 'Scott Mcdermott <scott@smemsh.net>'
__license__ = 'GPL-2.0'

import argparse # tmpl args

from sys import argv, stdin, stdout, stderr, exit
from subprocess import check_output

# tmpl getchar
from termios import tcgetattr, tcsetattr, TCSADRAIN
from tty import setraw

from os.path import basename
from os.path import dirname, isdir, exists # tmpl args
from os import (
    getenv,
    getcwd, chdir, makedirs, # tmpl dirs
    access, W_OK, # tmpl args
    close as osclose, # tmpl filter
    EX_OK as EXIT_SUCCESS,
    EX_SOFTWARE as EXIT_FAILURE,
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

# tmpl args
def process_args():

    global args

    def addopt(p, flagchar, longopt, help=None, /, **kwargs):
        options = list(("-%s --%s" % (flagchar, longopt)).split())
        p.add_argument(*options, help=help, **kwargs)

    def addarg(p, vname, vdesc, help=None, /, **kwargs):
        p.add_argument(vname, metavar=vdesc, help=help, **kwargs)

    def addflag(*args, **kwargs):
        addopt(*args, action='store_true', **kwargs)

    def addopts(*args, **kwargs):
        addopt(*args, action='store', **kwargs)

    def addtogg(*args, **kwargs):
        addopt(*args, action=argparse.BooleanOptionalAction, **kwargs)

    def addargs(*args, **kwargs):
        addarg(*args, nargs='*', **kwargs)

    # tmpl getchar
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

    # tmpl dirs
    addarg  (p, 'src', 'srcdir')
    addarg  (p, 'dest', 'destdir')

    args = p.parse_args(args)

    args.ask = True if not args.force else False

    if args.quiet and args.ask:
        bomb("quiet mode cannot be interactive")
    if args.dryrun and args.force:
        bomb("the force is not with you")

    # tmpl dirs
    src = args.src if args.src else getcwd()
    dst = args.dest if args.dest else getenv('HOME')
    for d in ['src', 'dst']: exec(f"{d} = {d}.rstrip('/')")

    # tmpl getchar
    if args.ask:
        action = 'test' if args.dryrun else 'do_something'
        print(f"{action} '{src}/ -> '{dst}/' (y/n)? ", end='')
        stdout.flush()
        yn = getchar(); print(yn)
        if yn != 'y': bomb('aborting')

    # tmpl dirs
    return abspath(src), abspath(dst)


# tmpl dirs
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

    # tmpl args
    src, dst = process_args()
    check_sanity(src, dst)

    # tmpl dirs
    try: chdir(src)
    except: bomb(f"cannot change directory to '{src}'")

    try: subprogram = globals()[invname]
    except (KeyError, TypeError):
        bomb(f"unimplemented command '{invname}'")

    try: return subprogram(src, dst)
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

    # tmpl filter
    # for filters, save stdin, pdb needs stdio fds itself
    if select([stdin], [], [], None)[0]:
        inbuf = stdin.read() # todo: problematic with large inputs
        osclose(stdin.fileno()) # cpython bug 73582
        try: stdin = open('/dev/tty')
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

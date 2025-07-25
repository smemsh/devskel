#!/usr/bin/env python3
"""
"""
__url__     = 'https://github.com/smemsh/devskel/'
__author__  = 'Scott Mcdermott <scott@smemsh.net>'
__license__ = 'GPL-2.0'
__devskel__ = '0.8.0'

from sys import exit, hexversion
if hexversion < 0x030900f0: exit("minpython: %s" % hexversion)

import argparse # tmpl args

from tty import setraw # tmpl getchar
from sys import argv # tmpl args
from sys import stdin # tmpl filter, getchar
from sys import stdout, stderr
from select import select # tmpl filter
from termios import tcgetattr, tcsetattr, TCSADRAIN # tmpl getchar
from subprocess import check_output # tmpl exe1
from subprocess import run, CalledProcessError # tmpl exe2

from os.path import basename
from os.path import dirname, isdir, exists, abspath # tmpl dirs
from os import (
    getenv, unsetenv,
    isatty, dup, # tmpl filter
    getcwd, chdir, makedirs, # tmpl dirs
    access, R_OK, W_OK, # tmpl dirs
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

# tmpl exe1 simple
def exe(cmd, **kwargs):
    return check_output(cmd.split(), **kwargs).splitlines()
    # if the lines should be decoded into strings rather than bytes
    #return check_output(cmd.split(), text=True).splitlines()

# tmpl exe2 complex
def exe(cmd, **kwargs):
    #defaults = dict(capture_output=True, check=True) # default is bytes
    defaults = dict(capture_output=True, check=True, text=True)
    kwargs = defaults | kwargs
    try: r = run(cmd.split(), **kwargs)
    except CalledProcessError as e:
        err(f"--> \"{cmd}\": returned {e.returncode}")
        for iostream in 'stdout', 'stderr':
            if buf := getattr(e, iostream):
                err(f"--> {iostream}:\n{buf}")
        bomb("aborting...")
    except FileNotFoundError:
        bomb(f"invocation failure: \"{cmd}\", aborting...")
    return r.stdout # tmpl exe2

###

# tmpl args
def process_args():

    global args

    def usagex(*args, **kwargs):
        nonlocal p
        p.print_help(file=stderr)
        print(file=stderr)
        bomb(*args, **kwargs)

    # parse_args() gives escaped strings
    def unesc(s):
        if s is None: return
        else: return s.encode('raw-unicode-escape').decode('unicode-escape')

    def addopt(p, flagchar, longopt, help=None, /, **kwargs):
        options = list(("-%s --%s" % (flagchar, longopt)).split())
        p.add_argument(*options, help=help, **kwargs)

    def addarg(p, vname, vdesc, help=None, /, **kwargs):
        p.add_argument(vname, metavar=vdesc, help=help, **kwargs)
        # if no need for different name in help than code
        #p.add_argument(vname, help=help, **kwargs)

    def addflag(*args, **kwargs):
        addopt(*args, action='store_true', **kwargs)

    def addopts(*args, **kwargs):
        addopt(*args, action='store', **kwargs)

    def addtogg(*args, **kwargs):
        addopt(*args, action=argparse.BooleanOptionalAction, **kwargs)

    def addnarg(*args, **kwargs):
        addarg(*args, nargs='?', **kwargs)

    def addargs(*args, **kwargs):
        addarg(*args, nargs='*', **kwargs)

    def hasopt(*options):
        return any([getattr(args, a) for a in [*options]])

    # tmpl getchar
    def getchar():
        fd = stdin.fileno()
        tattrs = tcgetattr(fd)
        setraw(fd)
        c = stdin.buffer.raw.read(1).decode(stdin.encoding)
        tcsetattr(fd, TCSADRAIN, tattrs)
        return c

    # tmpl
    # avoid initial 'usage:' line by providing as formatter_class and
    # providing empty string for 'usage'.  not clear why the interface
    # gives a prefix arg and defaults it, but doesn't allow it to be
    # passed in from anywhere, so we have to override
    #
    class RawTextHelpFormatterEmptyUsageLine(argparse.RawTextHelpFormatter):
        def add_usage(self, usage, actions, groups, prefix=None):
            if prefix is None:
                prefix = ''
            return super(RawTextHelpFormatterEmptyUsageLine, self) \
                .add_usage(usage, actions, groups, prefix)

    p = argparse.ArgumentParser(
        prog            = invname,
        description     = __doc__.strip(),
        allow_abbrev    = False,
        formatter_class = argparse.RawTextHelpFormatter,
        # tmpl
        #formatter_class = RawTextHelpFormatterEmptyUsageLine,
        #usage           = "",
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

    if debug == 1:
        breakpoint()

    # tmpl args
    src, dst = process_args()
    check_sanity(src, dst)

    # tmpl dirs
    try: chdir(src)
    except: bomb(f"cannot change directory to '{src}'")

    try: subprogram = globals()[invname]
    except (KeyError, TypeError):
        from inspect import trace
        if len(trace()) == 1: bomb("unimplemented")
        else: raise

    return subprogram(src, dst)

###

if __name__ == "__main__":

    invname = basename(argv[0])
    args = argv[1:]

    # tmpl filter
    # move stdin, pdb needs stdio fds itself
    stdinfd = stdin.fileno()
    if not isatty(stdinfd):
        try:
            if select([stdin], [], [])[0]:
                infile = open(dup(stdinfd))
                osclose(stdinfd)  # cpython bug 73582
                try: stdin = open('/dev/tty')
                except: pass  # no ctty, but then pdb would not be in use
        except KeyboardInterrupt:
            bomb("interrupted")
    else:
        bomb("must supply input on stdin")

    from bdb import BdbQuit
    if debug := int(getenv('DEBUG') or 0):
        import pdb
        from pprint import pp
        err('debug: enabled')
        unsetenv('DEBUG')  # otherwise forked children hang

    try: main()
    except BdbQuit: bomb("debug: stop")
    except SystemExit: raise
    except KeyboardInterrupt: bomb("interrupted")
    except:
        from traceback import print_exc
        print_exc(file=stderr)
        if debug: pdb.post_mortem()
        else: bomb("aborting...")
    finally:  # cpython bug 55589
        try: stdout.flush()
        finally:
            try: stdout.close()
            finally:
                try: stderr.flush()
                except: pass
                finally: stderr.close()

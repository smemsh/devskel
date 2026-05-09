#!/usr/bin/env python3
"""
"""
__url__     = 'https://github.com/smemsh/devskel/'
__author__  = 'Scott Mcdermott <scott@smemsh.net>'
__license__ = 'GPL-2.0'
__devskel__ = '0.11.3'

import sys
if sys.hexversion < 0x030a00f0:
    sys.exit("minpython: %s" % sys.hexversion)

import argparse # tmpl args

from tty import setraw # tmpl getchar
from shutil import which # tmpl envspawn
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
    spawnl, P_WAIT, # tmpl envspawn
    close as osclose, # tmpl filter
    EX_OK as EXIT_SUCCESS,
    EX_SOFTWARE as EXIT_FAILURE,
)

###

def msg(*args, **kwargs):
    print(*args, **kwargs)

def err(*args, **kwargs):
    msg(*args, file=sys.stderr, **kwargs)

def bomb(*args, **kwargs):
    err(*args, **kwargs)
    sys.exit(EXIT_FAILURE)

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

# tmpl exe3 envspawn
def envspawn(evar, default, arg):
    app = getenv(evar, default)
    cmd = which(app)
    spawnl(P_WAIT, cmd, basename(app), arg)

###

# tmpl args
def process_args():

    global args

    # tmpl mandatory (if we do usage-exit within this function)
    def usagex(*args, **kwargs):
        nonlocal p
        p.print_help(file=sys.stderr)
        print(file=sys.stderr)
        bomb(*args, **kwargs)

    # parse_args() gives escaped strings
    def unesc(s):
        if s is None: return
        else: return s.encode('raw-unicode-escape').decode('unicode-escape')

    def addopt(p, flagchar, longopt, help=None, /, **kwargs):
        options = list(("-%s --%s" % (flagchar, longopt)).split())
        p.add_argument(*options, help=help, **kwargs)

    # tmpl metavar
    #def addarg(p, vname, vdesc, help=None, /, **kwargs):
    #    p.add_argument(vname, metavar=vdesc, help=help, **kwargs)

    def addarg(p, vname, help=None, /, **kwargs):
        p.add_argument(vname, help=help, **kwargs)

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
        fd = sys.stdin.fileno()
        tattrs = tcgetattr(fd)
        setraw(fd)
        c = sys.stdin.buffer.raw.read(1).decode(sys.stdin.encoding)
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

    # tmpl mandatory
    if args is None: usagex("must supply data on stdin")
    if not args: usagex("must supply invocation arguments or options")

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
        sys.stdout.flush()
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

    # tmpl args
    invname = basename(sys.argv[0])
    args = sys.argv[1:]

    # tmpl filter, pipeout
    # move stdin [tmpl pipeout stdio], pdb needs them itself
    outfile = sys.stdout # tmpl pipeout
    stdinfd = sys.stdin.fileno()
    stdoutfd = sys.stdout.fileno() # tmpl pipeout

    # tmpl filter (only dup input, must invoke as filter)
    if not isatty(stdinfd):
        try:
            if select([sys.stdin], [], [])[0]:
                infile = open(dup(stdinfd))
                osclose(stdinfd)  # cpython bug 73582
                try: sys.stdin = open('/dev/tty')
                except: pass  # no ctty, but then pdb would not be in use
        except KeyboardInterrupt:
            bomb("interrupted")
    else:
        bomb("must supply data on stdin")

    # tmpl pipeout 1 (dup input+output, optionally invoked as filter)
    if isatty(stdinfd):
        # tmpl mandatory
        args = None
        # we want either empty or no stdin to trigger error later
        infile = open(devnull)
    else:
        # pdb will need stdio fds, so move and reopen
        try:
            if select([sys.stdin], [], [], 0)[0]:
                infile = open(dup(sys.stdinfd), 'r')
                outfile = open(dup(stdoutfd), 'a')
                for f in stdinfd, stdoutfd: osclose(f)
                try:
                    # tty must use fd 0/1 for pdb readline, cpython bug 73582
                    sys.stdin = open('/dev/tty', 'r')
                    sys.stdout = open('/dev/tty', 'a')
                except:
                    pass  # no ctty, but then pdb would not be in use
            else:
                bomb("must supply data on stdin")

        except KeyboardInterrupt:
            bomb("interrupted")
    # tmpl pipeout 1 end

    # tmpl pipeout 2 (dup input+output, must invoke as filter)
    if not isatty(stdinfd) and select([sys.stdin], [], [], 0)[0]:
        # pdb will need stdio fds, so move and reopen
        try:
            infile = open(dup(stdinfd), 'r')
            outfile = open(dup(stdoutfd), 'a')
            for f in stdinfd, stdoutfd: osclose(f)
            try:
                # tty must use fd 0/1 for pdb readline, cpython bug 73582
                sys.stdin = open('/dev/tty', 'r')
                sys.stdout = open('/dev/tty', 'a')
            except:
                pass  # no ctty, but then pdb would not be in use

        except KeyboardInterrupt:
            bomb("interrupted")
    else:
        bomb("must supply data on stdin")
    # tmpl pipeout 2 end

    from bdb import BdbQuit
    if debug := int(getenv('DEBUG') or 0):
        import pdb
        from os import getpid # tmpl stopsleep
        from time import sleep # tmpl stopsleep
        from pprint import pp
        err('debug: enabled') # tmpl stopsleep no
        err(f"debug: enabled for pid f{getpid()}") # tmpl stopsleep
        unsetenv('DEBUG')  # otherwise forked children hang
        # tmpl stopsleep
        if debug == 3:
            # allow attach from pdb since 3.14
            stopsleep = 0
            while not stopsleep:
                sleep(1)

    try: main()
    except BdbQuit: bomb("debug: stop")
    except SystemExit: raise
    except KeyboardInterrupt: bomb("interrupted")
    except:
        from traceback import print_exc
        print_exc(file=sys.stderr)
        if debug: pdb.post_mortem()
        else: bomb("aborting...")
    finally:  # cpython bug 55589
        try: sys.stdout.flush()
        finally:
            try: sys.stdout.close()
            finally:
                try: sys.stderr.flush()
                except: pass
                finally: sys.stderr.close()
    # tmpl pipeout
    finally:  # cpython bug 55589
        try:
            outfile.flush()
            sys.stdout.flush()
        finally:
            try:
                outfile.close()
                sys.stdout.close()
            finally:
                try: sys.stderr.flush()
                except: pass
                finally: sys.stderr.close()

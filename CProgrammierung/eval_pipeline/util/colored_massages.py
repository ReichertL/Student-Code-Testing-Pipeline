import sys

from util.colored_strings import ColoredString

"""
A set of functions for coloring strings for e.g. Passed,Warnings,Failed.
Colors: red, green ,yellow
"""

if sys.stdout.isatty():

    def red(s):
        return ColoredString('\033[1;31m' + s + '\033[0m', len(s))


    def green(s):
        return ColoredString('\033[32m' + s + '\033[0m', len(s))


    def yellow(s):
        return ColoredString('\033[1;33m' + s + '\033[0m', len(s))

else:

    def red(s):
        return s


    def green(s):
        return s


    def yellow(s):
        return s


class Warn:

    def __init__(self, warning):
        print(red('WARNING: ') + warning)


class Passed:
    def __init__(self, passed="passed"):
        print(green(passed))


class Failed:
    def __init__(self, failed="failed"):
        print(red(failed))


rc = {True: green('passed'),
      False: red('failed'),
      None: 'ignore'}


def redgreen(x, good):
    if good:
        return green(str(x))
    else:
        return red(str(x))


ind = {True: ' ', False: red('*')}


def errok(d):
    return green(str(d)) if d else red('failed')

"""
This module contains utility functions  relevant for testcase execution and evaluation
"""
import os
import tempfile
import logging
import subprocess


FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)





def unlink_safe(path):
    """
    Removes a file
    Parametes:
        path (string): file to remove
    """
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def unlink_as_cpr(path, sudo):
    """
    Removes a file as sudo
    Parametes:
        path (string): the file to remove
        sudo (string): path to sude executable
    """
    if os.path.exists(path):
        subprocess.call(sudo + ['rm', path])


def getmtime(path):
    """
    Returns the  mtime for a file. mtime is the file modification time.
    Parametes:
        path (string): the configuration to the file
    Returns:
        mtime (int)
    """
    return int(os.path.getmtime(path))


def sort_first_arg_and_diff(f1, f2):
    """
    Sorts and compares two files.
    Paremetes:
        f1 (string): path to file 1
        f2 (string): path to file 2
    Returns:
        res (bool): Contains whether the contents are equal or not.
    """
    f1_sorted = tempfile.mktemp()
    f2_sorted = tempfile.mktemp()
    subprocess.run(['sort', f1, '-o', f1_sorted])
    subprocess.run(['sort', f2, '-o', f2_sorted])
    res = (subprocess.run(['diff', '-q', f1_sorted, f2_sorted],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0)
    unlink_safe(f1_sorted)
    unlink_safe(f2_sorted)
    return res


def sudokill(process):
    """
    Calls kill on a process as sudo
    Parametes: 
        process (subprocess.Popen object):the process to kill
    """
    subprocess.call(['sudo', 'kill', str(process.pid)],
                    stderr=subprocess.DEVNULL)

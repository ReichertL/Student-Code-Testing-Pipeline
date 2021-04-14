"""
This module manages all test case execution and evaluation
"""
import datetime
import json
import os
import resource
import subprocess
import sys
import tempfile
import time
import logging

from logic.performance_evaluator import PerformanceEvaluator
from util.absolute_path_resolver import resolve_absolute_path
from util.colored_massages import Warn, Passed, Failed
from util.config_reader import ConfigReader
from util.gcc import hybrid_gcc, native_gcc
from util.named_pipe_open import NamedPipeOpen
from util.result_parser import ResultParser
from util.select_option import select_option_interactive
from logic.result_generator import ResultGenerator
from logic.load_tests import load_tests
from logic.retrieve_and_compile import retrieve_pending_submissions, compile_single_submission


from database.testcases import Testcase
from database.submissions import Submission
from database.runs import Run
from database.testcase_results import Testcase_Result
import database.database_manager as dbm
from database.students import Student
from database.valgrind_outputs import Valgrind_Output


FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)





def unlink_safe(path):
    """
    Removes a file
    :param path: file to remove
    """
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def unlink_as_cpr(path, sudo):
    """
    Removes a file as sudo
    :param path: the file to remove
    :param sudo: call params as sudo
    """
    if os.path.exists(path):
        subprocess.call(sudo + ['rm', path])


def getmtime(path):
    """
    returns the mtime for a file
    :param path: the configuration to the file
    :return: the mtime
    """
    return int(os.path.getmtime(path))


def sort_first_arg_and_diff(f1, f2):
    """
    Sorts and compares two files
    :param f1: file 1
    :param f2: file 2
    :return: whether the content is equal or not
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
    :param process: the process to kill
    """
    subprocess.call(['sudo', 'kill', str(process.pid)],
                    stderr=subprocess.DEVNULL)

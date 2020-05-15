"""
This module manages all test case execution and evaluation
"""
import os
import subprocess

from logic.config_reader import ConfigReader
from models.compilation import Compilation

BASE_DIR = "/home/mark/Uni/SHK2020/ds/CProgrammierung/musterloesung/"
MUSTERLOESUNG_DIR = "Musterloesung_Mark/loesung.c"


class TestCaseExecutor:
    """
    TestCaseExecutor:
    manages test case execution and compilation as well as reporting
    :parameter
        args :  parsed commandline arguments
    """
    args = {}
    configuration = ""

    def __init__(self, args):
        config_path = "./resources/config_test_case_executor.config"
        configuration = ConfigReader().read_file(os.path.abspath(config_path))
        self.configuration = configuration
        self.args = args

    def run(self):
        """
            runs specified test cases
        """
        compilation_only = len(self.args.compile) > 0

        pending_submissions = self.retrieve_pending_submissions()

        for i in pending_submissions:
            print(i)
            self.compile_single_submission(i)
            if not compilation_only:
                pass

        print("executing test cases")

    def retrieve_pending_submissions(self):
        """Extracts submissions that should be evaluated
        based on the commandline arguments
        :return: list of submissions
        """
        submissions = [f"{BASE_DIR}{MUSTERLOESUNG_DIR}"]

        print(self.args)
        if self.args.check:
            print("TODO: retrieving only untested submissions")

        if self.args.all:
            print("TODO: retrieving all submissions")

        if len(self.args.compile) > 0:
            print("TODO: retrieving one submission only for compilation")

        if len(self.args.extra_sources) > 0:
            print("TODO: retrieving one submission only for compilation")

        for submission in submissions:
            compilation = self.compile_single_submission(submission)
            print(compilation)
        return submissions

    def compile_single_submission(self, path: str, strict=True):
        """Tries to compile a c file at path
        @:param path string describing the path of the path c file
        @:param strict
                boolean describing whether
                -Werror' should be used as gcc flag
        @:return Compilation object
                (gcc_return_code, commandline call , gcc_stderr)
        """

        gcc_args = [self.configuration["GCC_PATH"], '-o', 'loesung'] + \
                   self.configuration["CFLAGS"]
        if not strict:
            gcc_args.remove('-Werror')

        all_args = gcc_args + \
                   self.configuration["CFLAGS_LOCAL"] + \
                   [os.path.abspath(path)]
        cp = subprocess.run(all_args,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE,
                            universal_newlines=True,
                            errors='ignore',
                            cwd='/tmp', check=False)
        return Compilation(return_code=cp.returncode,
                           commandline=' '.join(all_args),
                           output=cp.stderr)

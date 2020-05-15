"""
This module manages all test case execution and evaluation
"""
import os
import subprocess

from models.compilation import Compilation
from models.test_case import TestCase
from util.config_reader import ConfigReader

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
    test_cases = {}

    def __init__(self, args):
        config_path = "./resources/config_test_case_executor.config"
        configuration = ConfigReader().read_file(os.path.abspath(config_path))
        self.configuration = configuration
        self.test_cases = self.load_tests()
        self.args = args

    def run(self):
        """
            runs specified test cases
        """
        compilation_only = len(self.args.compile) > 0
        self.load_tests()
        pending_submissions = self.retrieve_pending_submissions()

        for i in pending_submissions:
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

        if self.args.check:
            print("TODO: retrieving only untested submissions")

        if self.args.all:
            print("TODO: retrieving all submissions")

        if len(self.args.compile) > 0:
            print("TODO: retrieving one submission only for compilation")

        if len(self.args.extra_sources) > 0:
            print("TODO: retrieving one submission only for compilation")

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

    def load_tests(self):
        """
        Loads the in the config file specified testcases for good bad and extra
        :return: dictionary of dictionaries of pairs type -> path -> (input, output)
        """
        test_cases = {}
        extensions = {"BAD": self.configuration["TESTS_BAD_EXTENSION"],
                      "GOOD": self.configuration["TESTS_GOOD_EXTENSION"],
                      "EXTRA": self.configuration["TESTS_EXTRA_EXTENSION"]}

        for key in extensions:

            test_case_input = {}
            for root, _, files in os.walk(

                    os.path.join(self.configuration["TESTS_BASE_DIR"], extensions[key]),
                    topdown=False):
                for name in files:

                    path = os.path.join(root, name).replace(".stdin", "").replace(".stdout", "")

                    if path not in test_case_input:
                        test_input = ""
                        test_output = ""
                        with open(f"{path}.stdin") as input_file:
                            test_input = input_file.read()
                        if key != "BAD":
                            with open(f"{path}.stdout") as output_file:
                                test_output = output_file.read()

                        test_case = TestCase(path, test_input, test_output, key == "BAD")
                        print(test_case)
                        test_case_input.update({path: (test_input, test_output)})

                        path_mapping = [(key, test_case_input)]

                        test_cases.update(path_mapping)

        return test_cases

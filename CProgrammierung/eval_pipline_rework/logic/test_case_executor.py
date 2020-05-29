"""
This module manages all test case execution and evaluation
"""
import os
import subprocess
import sys
import tempfile
from datetime import time

from models.compilation import Compilation
from models.submission import Submission
from models.test_case import TestCase
from models.test_case_result import TestCaseResult
from util.config_reader import ConfigReader
from util.colored_massages import Warn, Passed, Failed

BASE_DIR = "/home/mark/Uni/SHK2020/ds/CProgrammierung/musterloesung/"
MUSTERLOESUNG_DIR = "Musterloesung_Mark/loesung.c"


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
    :param path: the path to the file
    :return: the mtime
    """
    return int(os.path.getmtime(path))


def sort_first_arg_and_diff(f1, f2):
    f1_sorted = tempfile.mktemp()
    subprocess.run(['sort', f1, '-o', f1_sorted])
    res = (0 == subprocess.run(['diff', '-q', f1_sorted, f2],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL).returncode)
    unlink_safe(f1_sorted)
    return res


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
    sudo_path = ''
    sudo_user = ''
    sudo = [sudo_path, '-u', sudo_user]

    def __init__(self, args):
        config_path = "./resources/config_test_case_executor.config"
        configuration = ConfigReader().read_file(os.path.abspath(config_path))
        self.configuration = configuration
        self.test_cases = self.load_tests()
        self.args = args
        self.sudo_path = configuration["sudo_path"]
        self.sudo_user = configuration["sudo_user"]
        self.sudo = [self.sudo_path, '-u', self.sudo_user]

    def run(self, database_manager):
        """
            runs specified test cases
        """
        compilation_only = len(self.args.compile) > 0
        self.load_tests()
        pending_submissions = self.retrieve_pending_submissions(
            database_manager)

        for i in pending_submissions:
            self.compile_single_submission(i)
            if not compilation_only:
                pass

        print("executing test cases")

    def retrieve_pending_submissions(self, database_manager):
        """Extracts submissions that should be evaluated
        based on the commandline arguments
        :return: list of submissions
        """
        submissions = [f"{BASE_DIR}{MUSTERLOESUNG_DIR}"]
        students = []
        if self.args.check:
            print("TODO: retrieving only untested submissions")

        if self.args.all:
            students = database_manager.get_all_students()

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
        :return: dictionary of dictionaries of pairs
        test_case_type -> path -> (input, output)
        """
        test_cases = {}
        extensions = {"BAD": self.configuration["TESTS_BAD_EXTENSION"],
                      "GOOD": self.configuration["TESTS_GOOD_EXTENSION"],
                      "EXTRA": self.configuration["TESTS_EXTRA_EXTENSION"]}

        for key in extensions:

            test_case_input = []
            for root, _, files in os.walk(

                    os.path.join(self.configuration["TESTS_BASE_DIR"],
                                 extensions[key]),
                    topdown=False):
                for name in files:

                    path = os.path.join(root, name). \
                        replace(".stdin", ""). \
                        replace(".stdout", "")

                    if path not in test_case_input:
                        test_input = ""
                        test_output = ""
                        with open(f"{path}.stdin") as input_file:
                            test_input = input_file.read()
                        if key != "BAD":
                            with open(f"{path}.stdout") as output_file:
                                test_output = output_file.read()

                        test_case = TestCase(path, test_input, test_output, error_expected=(key == "BAD"))
                        test_case_input.append(test_case)

            path_mapping = [(key, test_case_input)]
            test_cases.update(path_mapping)

        self.test_cases = test_cases
        return test_cases

    def check(self, student,
              submission,
              force=False,
              verbose=True,
              force_performance=False,
              strict=True):
        """
        checks the submission of a student
        :param student: the student which is the author of this submission
        :param submission: the submission to test
        :param force: this forces a rerun
        :param verbose: enables vebose output
        :param force_performance: tests test_cases for performance too
        :param strict: manipulates compiler flags
        :return: true if a check was cunducted, else false
        """

        source = submission.path
        mtime = getmtime(source)
        timestamp = int(time.time())
        if submission.is_checked:
            if force:
                Warn(f'You forced to re-run tests on submission by '
                     f'{student.name}, submitted on {submission.mtime}.')
            else:
                return False
        print(f'running tests for {student.name} ', end='')
        sys.stdout.flush()
        submission = Submission(timestamp=timestamp,
                                mtime=mtime,
                                compilation=compile(source, strict),
                                fast=False,
                                timing=None)
        if submission.compilation.return_code == 0:
            submission.tests_bad_input = {
                p: self.check_for_error(p, verbose)
                for p in self.test_cases["BAD"]}
            submission.tests_good_input = {
                p: self.check_output(p, verbose, sort_first_arg_and_diff)
                for p in self.test_cases["GOOD"]}
        if submission and (submission.is_performant()
                           or force_performance):
            print('fast submission; running performance tests')
            submission.tests_performance = {
                p: self.check_output(p, verbose)
                for p in self.test_cases["EXTRA"]}
        if submission:
            Passed()
        else:
            Failed()
            if verbose:
                submission.print_stats()
        student.submissions[str(mtime)] = submission
        return True

    def check_for_error(self, submission, path, verbose):
        """
        checks a submission for a bad input test case
        :param submission: the submission to test
        :param path: path to the test case
        :param verbose: enables verbose output
        :return: returns the result of the testcase
        """
        assert path in self.test_cases['BAD']
        test_case_result = self.execute_test_case(submission, path, verbose)
        test_case_result.error_line = ''
        # Todo:evaluate error msg
        test_case_result.output_correct = True
        unlink_safe('test.stderr')
        unlink_safe('test.stdout')
        return test_case_result

    def check_output(self, path, submission, verbose, comparator):
        """
        Checks a testcase that should be successful
        :param path: path to test case
        :param submission: submission to test
        :param verbose: enables verbose input
        :param comparator: compares to results
        :return: a TestCaseResult object encapsulating the results
        """
        test_case_result = self.execute_test_case(submission, path, verbose)
        test_case_result.output_correct = comparator('test.stdout',
                                                     os.path.join('testcases', path + '.stdout'))
        unlink_safe('test.stderr')
        unlink_safe('test.stdout')
        return test_case_result

    def execute_test_case(self, submission, path, verbose):
        """
        tests a submission with a testcase
        :param submission: the submission to test
        :param path: the path to the test case
        :param verbose: enables verbose output
        :return: returns a test_case_result object
        """
        # Todo: reimplement run lsg
        return TestCaseResult(path)

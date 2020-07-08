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

from logic.performance_evaluator import PerformanceEvaluator
from models.compilation import Compilation
from models.test_case import TestCase
from models.test_case_result import TestCaseResult
from util.absolute_path_resolver import resolve_absolute_path
from util.colored_massages import Warn, Passed, Failed
from util.config_reader import ConfigReader
from util.named_pipe_open import NamedPipeOpen
from util.result_parser import ResultParser


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
    f1_sorted = tempfile.mktemp()
    f2_sorted = tempfile.mktemp()
    subprocess.run(['sort', f1, '-o', f1_sorted])
    subprocess.run(['sort', f2, '-o', f2_sorted])
    res = (0 == subprocess.run(['diff', '-q', f1_sorted, f2_sorted],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL).returncode)
    unlink_safe(f1_sorted)
    unlink_safe(f2_sorted)
    return res


def sudokill(process):
    subprocess.call(['sudo', 'kill', str(process.pid)],
                    stderr=subprocess.DEVNULL)


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
    unshare_path = ""
    unshare = [unshare_path, '-r', '-n']

    def __init__(self, args):

        config_path = resolve_absolute_path("/resources/config_test_case_executor.config")

        configuration = ConfigReader().read_file(os.path.abspath(config_path))
        self.configuration = configuration
        # self.test_cases = self.load_tests()
        self.args = args
        self.sudo_path = configuration["SUDO_PATH"]
        self.sudo_user = configuration["SUDO_USER"]
        self.sudo = [self.sudo_path, '-u', self.sudo_user]

        self.unshare_path = configuration["UNSHARE_PATH"]
        self.unshare = [self.unshare_path, '-r', '-n']

    def run(self, database_manager, verbosity):
        """
            runs specified test cases
        """
        self.test_cases = self.load_tests(database_manager)

        pending_submissions = self.retrieve_pending_submissions(
            database_manager)

        for student_key in pending_submissions.keys():
            current_student = database_manager.get_student_by_key(student_key)
            for unchecked_submission in pending_submissions[student_key]:

                compilation_result = self.compile_single_submission(unchecked_submission.path)
                unchecked_submission.compilation = compilation_result

                database_manager.insert_compilation_result(current_student,
                                                           unchecked_submission, compilation_result)

                if not len(self.args.compile) > 0:
                    test_case_results = self.check(current_student, unchecked_submission)
                    if test_case_results:
                        for test_case_result in test_case_results:
                            database_manager.insert_test_case_result(current_student, unchecked_submission,
                                                                     test_case_result)
                    database_manager.set_submission_checked(unchecked_submission)
                    if unchecked_submission.passed:
                        database_manager.set_student_passed(current_student)
                result = database_manager.get_test_case_result(current_student, unchecked_submission)

    def retrieve_pending_submissions(self, database_manager):
        """Extracts submissions that should be evaluated
        based on the commandline arguments
        :return: list of submissions
        """

        submissions = {}
        students = []
        if self.args.check:
            for i in self.args.check:
                students.append(database_manager.get_student_by_name(i))

        if self.args.all:
            students = database_manager.get_all_students()

        for student in students:
            student.get_all_submissions(database_manager)
            unchecked_submissions = []
            if student.submissions is not None:
                if not self.args.rerun:
                    unchecked_submissions = student.get_unchecked_submissions()
                else:
                    unchecked_submissions = student.submissions
            if len(unchecked_submissions) > 0:
                submissions.update({student.data_base_key: unchecked_submissions})

        return submissions

    def compile_single_submission(self, path: str, strict=True):
        """Tries to compile a c file at configuration
        @:param configuration string describing the configuration of the configuration c file
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

    def load_tests(self, database_manager):
        """
        Loads the in the config file specified testcases for good bad and extra
        :return: dictionary of list test_case
        test_case_type -> [test_cases]
        """
        test_cases = {}
        extensions = {"BAD": self.configuration["TESTS_BAD_EXTENSION"],
                      "GOOD": self.configuration["TESTS_GOOD_EXTENSION"],
                      "EXTRA": self.configuration["TESTS_EXTRA_EXTENSION"]}
        id = 0
        json_descriptions = {}

        for key in extensions:

            test_case_input = []
            path_prefix = os.path.join(self.configuration["TESTS_BASE_DIR"],
                                       extensions[key])
            for root, _, files in os.walk(
                    path_prefix
                    ,
                    topdown=False):
                for name in files:

                    if name.endswith(".json"):
                        with open(os.path.join(root, name)) as description_file:
                            short_id = name.replace(".json", "")
                            description = json.load(description_file)
                            json_descriptions.update({short_id: description})

                    if not name.endswith('.stdin'):
                        continue

                    path = os.path.join(root, name). \
                        replace(".stdin", ""). \
                        replace(".stdout", "")

                    test_output = ""
                    with open(f"{path}.stdin") as input_file:
                        test_input = input_file.read()
                    if key != "BAD":
                        with open(f"{path}.stdout") as output_file:
                            test_output = output_file.read()

                    test_case = TestCase(path, test_input, test_output, error_expected=(key == "BAD"))
                    test_case.type = key
                    test_case_input.append(test_case)

            path_mapping = [(key, test_case_input)]
            test_cases.update(path_mapping)
        all_test_cases = []

        for key in test_cases:
            for test_case in test_cases[key]:
                test_case.valgrind_needed = False if key == "EXTRA" else True
                test_case.type_good_input = False if key == "BAD" else True
                test_case.id = id
                try:
                    test_case.description = json_descriptions[test_case.short_id]["short_desc"]
                except KeyError:
                    test_case.description = test_case.short_id
                try:
                    test_case.hint = json_descriptions[test_case.short_id]["hint"]
                except KeyError:
                    test_case.hint = f"bei {test_case.short_id}"

                id = id + 1
                database_manager.insert_test_case_information(test_case)
                all_test_cases.append(test_case)

        test_cases.update([("ALL", all_test_cases)])

        return test_cases

    def check(self, student,
              submission,
              force_performance=False,
              strict=True):
        """
        checks the submission of a student
        :param student: the student which is the author of this submission
        :param submission: the submission to test
        :param force_performance: tests test_cases for performance too
        :param strict: manipulates compiler flags
        :return: true if a check was conducted, else false
        """

        source = submission.path
        if submission.is_checked:
            if self.args.rerun:
                Warn(f'You forced to re-run tests on submission by '
                     f'{student.name} submitted at {submission.timestamp}.\n'

                     f'This is the {submission.submission_key + 1}. submission, saved as {submission.path}')
            else:
                return False
        print(f'running tests for {student.name} submitted at {submission.timestamp}')
        sys.stdout.flush()
        submission.compilation = self.compile_single_submission(source)
        all_results = []

        bad_input_results = []
        good_input_results = []
        extra_input_results = []
        if submission.compilation.return_code == 0:
            for test in self.test_cases["BAD"]:
                result = self.check_for_error(submission, test)
                result.type = "BAD"
                result.type_good_input = False
                result.id = test.id
                bad_input_results.append(result)
            for test in self.test_cases["GOOD"]:
                result = self.check_output(submission, test, sort_first_arg_and_diff)
                result.type = "GOOD"
                result.id = test.id
                good_input_results.append(result)

        passed = submission.compilation.return_code == 0
        for i in bad_input_results:
            all_results.append(i)
        for i in good_input_results:
            all_results.append(i)
        for i in all_results:
            passed = passed and i.passed()

        submission.is_checked = True
        submission.timestamp = datetime.datetime.now()
        student.passed = student.passed or passed
        if submission.passed:
            performance_evaluator = PerformanceEvaluator()
            performance_evaluator.evaluate_performance(submission)
        if submission and (submission.is_performant()
                           or force_performance):
            print('fast submission; running performance tests')
            for test in self.test_cases["EXTRA"]:
                result = self.check_output(submission, test, sort_first_arg_and_diff)
                result.type = "EXTRA"
                result.id = test.id
                extra_input_results.append(result)

        for i in extra_input_results:
            all_results.append(i)

        submission.tests_good_input = good_input_results
        submission.tests_bad_input = bad_input_results
        submission.tests_extra_input = extra_input_results

        if submission.passed and submission.is_performant():
            performance_evaluator.average_euclidean_cpu_time_competition(submission)
            Passed()

        else:
            Failed()
            if self.args.verbose:
                submission.print_stats()
        return all_results

    def check_for_error(self, submission, test):
        """
        checks a submission for a bad input test case
        :param submission: the submission to test
        :param test: test case to execute
        :param verbose: enables verbose output
        :return: returns the result of the testcase
        """
        test_case_result = self.execute_test_case(test, submission)
        test_case_result.error_line = ''
        test_case_result.output_correct = True
        parser = ResultParser()
        parser.parse_error_file(test_case_result)
        if test_case_result.return_code > 0 and test_case_result.error_msg_quality > 0:
            test_case_result.output_correct = True
        else:
            test_case_result.output_correct = False
        unlink_safe("test.stderr")
        unlink_safe("test.stdout")
        test_case_result.student_key = submission.student_key
        test_case_result.submission_key = submission.submission_key
        return test_case_result

    def check_output(self, submission, test, comparator):
        """
        Checks a testcase that should be successful
        :param test: test case to execute
        :param submission: submission to test
        :param verbose: enables verbose input
        :param comparator: compares to results
        :return: a TestCaseResult object encapsulating the results
        """
        test_case_result = self.execute_test_case(test, submission)
        test_case_result.output_correct = comparator('test.stdout',
                                                     os.path.join(test.path + '.stdout'))
        unlink_safe("test.stderr")
        unlink_safe("test.stdout")
        test_case_result.student_key = submission.student_key
        test_case_result.submission_key = submission.submission_key

        return test_case_result

    def execute_test_case(self, test_case, submission):
        """
        tests a submission with a testcase
        :param submission: the submission to test
        :param test_case: the test_case object encapsulating
        paths and expected results
        :param verbose: enables verbose output
        :return: returns a test_case_result object
        """
        input_path = test_case.path + ".stdin"
        tic = time.time()
        parser = ResultParser()
        if self.args.verbose:
            print(f'--- executing {"".join(submission.path.split("/")[-2:])} < {test_case.short_id} ---')
        with NamedPipeOpen(input_path) as fin, \
                open('test.stdout', 'bw') as fout, \
                open('test.stderr', 'bw') as ferr:
            args = ['./loesung']
            p = subprocess.Popen(
                self.sudo + self.unshare + [self.configuration["TIME_PATH"], "-f", '%S %U %M %x %e', '-o',
                                            self.configuration["TIME_OUT_PATH"]] + args,
                stdin=fin,
                stdout=fout,
                stderr=ferr,
                preexec_fn=self.set_limits_time,
                cwd='/tmp')
            try:
                p.wait(150)
            except subprocess.TimeoutExpired:
                sudokill(p)
            duration = time.time() - tic
            result = TestCaseResult(test_case.path)
            result.return_code = p.returncode
            if p.returncode in (-9, -15, None):
                result.timeout = False
                result.return_code = p.returncode
                if result.return_code is None:
                    result.return_code = -15
                duration = -1
            else:
                with open(self.configuration["TIME_OUT_PATH"]) as file:
                    parser.parse_time_file(test_case_result=result, file=file)
            if self.args.verbose and not result.timeout:
                print('-> TIMEOUT')
            result.tictoc = duration
            fin.close()

            if self.args.verbose:
                print(f'--- finished {"".join(submission.path.split("/")[-2:])} < {test_case.short_id} ---')

        result.vg['ok'] = None
        if test_case.valgrind_needed and result.timeout and result.segfault:
            if self.args.verbose:
                print(f'--- executing valgrind {"".join(submission.path.split("/")[-2:])} < {test_case.short_id} ---')
            with NamedPipeOpen(input_path) as fin:
                p = subprocess.Popen(self.sudo + self.unshare + [self.configuration["VALGRIND_PATH"],
                                                                 '--log-file=' + self.configuration[
                                                                     "VALGRIND_OUT_PATH"]] + args,
                                     stdin=fin,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL,
                                     preexec_fn=self.set_limits_valgrind,
                                     cwd='/tmp')
                try:
                    p.wait(300)
                except subprocess.TimeoutExpired:
                    sudokill(p)
            if p.returncode not in (-9, -15, None):
                try:
                    with open(self.configuration["VALGRIND_OUT_PATH"], 'br') as f:
                        result.vg = parser.parse_valgrind_file(f)
                except FileNotFoundError:
                    pass
            if self.args.verbose:
                print(f'--- finished valgrind {"".join(submission.path.split("/")[-2:])} < {test_case.short_id} ---')
            result.description = test_case.description
            result.hint = test_case.hint
            unlink_as_cpr(self.configuration["VALGRIND_OUT_PATH"], self.sudo)
        return result

    def set_limits_time(self):
        resource.setrlimit(resource.RLIMIT_DATA, 2 * (self.configuration["RLIMIT_DATA"],))
        resource.setrlimit(resource.RLIMIT_STACK, 2 * (self.configuration["RLIMIT_STACK"],))
        resource.setrlimit(resource.RLIMIT_CPU, 2 * (self.configuration["RLIMIT_CPU"],))

    def set_limits_valgrind(self):
        resource.setrlimit(resource.RLIMIT_DATA, 2 * (self.configuration["VALGRIND_DATA"],))
        resource.setrlimit(resource.RLIMIT_STACK, 2 * (self.configuration["VALGRIND_STACK"],))
        resource.setrlimit(resource.RLIMIT_CPU, 2 * (self.configuration["VALGRIND_CPU"],))

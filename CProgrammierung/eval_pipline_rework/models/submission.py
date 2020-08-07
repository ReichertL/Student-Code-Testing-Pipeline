"""
Data abstraction for a submission by a specific student
"""
import os
import sys
from datetime import datetime

from models.compilation import Compilation
from util.colored_massages import red, yellow, green
from util.htable import table_format

hline = 110 * '-'


class Submission:
    """
        Data abstraction for a submission by a specific student
    """
    student_key: int = -1
    submission_key: int = -1
    timestamp: datetime = datetime.now()
    path = ""
    is_checked = False
    fast: bool = False
    mtime: int = -1
    timing: dict
    compilation: Compilation = None
    # passed = False
    performant = True
    tests_bad_input = []
    tests_good_input = []
    tests_extra_input = []

    def __init__(self, timestamp=None, mtime=-1, compilation=None, fast=False, timing=None):
        if timestamp is not None:
            self.timestamp = timestamp
        if mtime != -1:
            self.mtime = mtime
        if compilation is not None:
            self.compilation = compilation
        if fast:
            self.fast = fast
        if timing is not None:
            self.timing = timing

    def __str__(self):
        """
        Returns a string representation of the submission object
        :return: string representation of the submission object
        """

        return f"Submission(" \
               f"\n\tstudent_key={self.student_key}" \
               f" submission_key={self.submission_key}" \
               f" timestamp={self.timestamp}" \
               f" path={self.path}" \
               f" is_checked={self.is_checked}" \
               f" fast={self.fast}" \
               f" mtime={self.mtime} " \
               f" passed={self.passed} " \
               f"\n\t\tCompilation({self.compilation})" \
               f"\n)"

    @property
    def passed(self):
        passed = True
        if self.compilation is None:
            return False
        passed = passed and self.compilation.return_code == 0
        for bad_test in self.tests_bad_input:
            passed = passed and bad_test.passed()
        for good_test in self.tests_good_input:
            passed = passed and good_test.passed()

        return passed

    def __bool__(self):
        return True if self.passed else False

    def is_performant(self):
        return self.performant

    def print_small_stats(self, f=sys.stdout):
        map_to_int = lambda test_case_result: 1 if test_case_result.passed() else 0
        output = f'{self.path.split(os.path.sep)[-1]}: '
        if not self.compilation:
            output = output + (red('Compilation failed. '))
            print(output)
            return

        output = output + (green('Compilation successful. '))

        failed = len(self.tests_bad_input) - sum(map(map_to_int, self.tests_bad_input))
        all = len(self.tests_bad_input)
        if failed > 0:
            output = output + (red(f'{failed} / {all} bad tests failed. '))
        else:
            output = output + (green(f'{failed} / {all} bad tests failed. '))

        failed = len(self.tests_good_input) - sum(map(map_to_int, self.tests_good_input))
        all = len(self.tests_good_input)
        if failed > 0:
            output = output + (red(f'{failed} / {all} good tests failed. '))
        else:
            output = output + (green(f'{failed} / {all} good tests failed. '))

        print(output, file=f)

    def print_stats(self, f=sys.stdout):
        map_to_int = lambda test_case_result: 1 if test_case_result.passed() else 0
        if not self.compilation:
            print(red('compilation failed; compiler errors follow:'), file=f)
            print(hline, file=f)
            print(self.compilation.commandline, file=f)
            print(self.compilation.output, file=f)
            print(hline, file=f)
            return
        if len(self.compilation.output) > 0:
            print(yellow('compilation procudes the following warnings:'), file=f)
            print(hline, file=f)
            print(self.compilation.commandline, file=f)
            print(self.compilation.output, file=f)
            print(hline, file=f)
        passed_bad = True
        for bad_test in self.tests_bad_input:
            passed_bad = passed_bad and bad_test.passed()
        if passed_bad:
            print(green('All tests concerning malicious input passed.'), file=f)
        else:
            failed = len(self.tests_bad_input) - sum(map(map_to_int, self.tests_bad_input))
            all = len(self.tests_bad_input)
            print(red(f'{failed} / {all} tests concerning malicious input failed.')
                  , file=f)
            print(file=f)
            self.tests_bad_input.sort(key=lambda x: x.short_id)
            print(table_format(
                '{id} | {valgrind} | {valgrind_rw} | {segfault} | {timeout} | {return} | {err_msg} | {description}',
                [x.statistics_dict for x in self.tests_bad_input],
                titles='auto'), file=f)
            print(file=f)

        passed_good = True
        for good_test in self.tests_good_input:
            passed_good = passed_good and good_test.passed()
        if passed_good:
            print(green('All tests concerning good input passed.'), file=f)
        else:
            failed = len(self.tests_good_input) - sum(map(map_to_int, self.tests_good_input))
            all = len(self.tests_good_input)
            print(red(f'{failed} / {all} tests concerning good input failed.')
                  , file=f)
            print(file=f)
            self.tests_good_input.sort(key=lambda x: x.short_id)
            print(table_format(
                '{id} | {valgrind} | {valgrind_rw} | {segfault} | {timeout} | {return} | {output} | {description}',
                [x.statistics_dict for x in self.tests_good_input],
                titles='auto'), file=f)
            print(file=f)

"""
Data abstraction for a submission by a specific student
"""
from datetime import datetime
from typing import Dict

from models.compilation import Compilation
from models.test_case_result import TestCaseResult


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

    tests_bad_input: Dict[str, TestCaseResult]
    tests_good_input: Dict[str, TestCaseResult]
    tests_performance: Dict[str, TestCaseResult]

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
               f"\n\t{self.student_key}" \
               f" {self.submission_key}" \
               f" {self.timestamp}" \
               f" {self.path}" \
               f" {self.is_checked}" \
               f" {self.fast}" \
               f" {self.mtime} " \
               f"\n\t\t{self.compilation}" \
               f"\n)"

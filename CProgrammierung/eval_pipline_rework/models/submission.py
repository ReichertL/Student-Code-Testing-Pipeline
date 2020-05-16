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
    timestamp: datetime = None
    mtime: int = -1
    tests_bad_input: Dict[str, TestCaseResult]
    tests_good_input: Dict[str, TestCaseResult]
    tests_performance: Dict[str, TestCaseResult]
    compilation: Compilation
    fast: bool = False
    timing: dict

    def __init__(self):
        self.timestamp = datetime.now()


    def __str__(self):
        """
        Returns a string representation of the submission object
        :return: string representation of the submission object
        """

        return f"{self.student_key} {self.submission_key} {self.timestamp}"

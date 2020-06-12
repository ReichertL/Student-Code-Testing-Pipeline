"""
Data abstraction for a submission by a specific student
"""
from datetime import datetime

from models.compilation import Compilation


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
    passed = False
    is_performant = True

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

    def __bool__(self):
        return self.passed

    def is_performant(self):
        return self.is_performant

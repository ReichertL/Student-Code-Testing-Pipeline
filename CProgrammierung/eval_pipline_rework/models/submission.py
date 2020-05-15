from typing import Dict

from models.compilation import Compilation
from models.test_case_results import TestCaseResults


class Submission:
    timestamp: int = -1
    mtime: int = -1
    tests_bad_input: Dict[str, TestCaseResults]
    tests_good_input: Dict[str, TestCaseResults]
    tests_performance: Dict[str, TestCaseResults]
    compilation: Compilation
    fast: bool = False
    timing: dict

"""
Contains abstractions for the test_case_results
"""


class TestCaseResult:
    """
    Abstraction for the test_case_results
    """
    student_key: int = -1
    submission_key: int = -1
    type: str = ""
    path = ''

    # id: str = ''
    # vg: dict
    # ignore: list = []
    # type_good_input: bool = True
    # signal: int = 0
    # segfault: bool = True
    # timeout: bool = True
    # cpu_time: float = None
    # realtime: float = None
    # tictoc: float = None
    # mrss: int = -1
    # return_code: int = -128
    # output_correct: bool = False
    # error_msg_quality: int = -1
    # error_line: str = ''

    def __init__(self, test_case_identifier):
        self.path = test_case_identifier

    def __str__(self):
        """
        Returns a pretty printed string representation
        of the TestCaseResult Object
        :return: Pretty Printed String
        """
        return f"TestCaseResult(" \
               f"\n\tstudent_key={self.student_key}," \
               f"\n\tsubmission_key={self.submission_key}," \
               f"\n\tpath={self.path}\n" \
               f")"

    def get_database_entry(self):
        """
        Returns all values which shall be inserted in a database
        :return: all values representing the result
        """
        return [
            self.path

        ]

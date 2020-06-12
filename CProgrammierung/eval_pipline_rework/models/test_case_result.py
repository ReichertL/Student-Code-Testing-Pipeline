"""
Contains abstractions for the test_case_results
"""


class TestCaseResult:
    """
    Abstraction for the test_case_results
    """
    student_key: int = -1
    submission_key: int = -1
    id = -1
    type: str = ""
    path: str = ""
    error_line: str = ''
    error_msg_quality: int = -1
    output_correct: bool = False
    return_code: int = -128
    type_good_input: bool = True
    signal: int = 0
    segfault: bool = True
    timeout: bool = True
    cpu_time: float = None
    realtime: float = None
    tictoc: float = None
    mrss: int = -1

    vg = {}
    ignore: list = []

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
               f"\n\ttype={self.type}," \
               f"\n\ttype_good_input={self.type_good_input}," \
               f"\n\tpath={self.path}" \
               f"\n\terror_line={self.error_line}" \
               f"\n\terror_massage_quality={self.error_msg_quality}" \
               f"\n\treturn_code={self.return_code}" \
               f"\n\tsignal={self.signal}" \
               f"\n\tsegfault={self.segfault}" \
               f"\n\ttimeout={self.timeout}" \
               f"\n\tcputime={self.cpu_time}" \
               f"\n\trealtime={self.realtime}" \
               f"\n\ttictoc={self.tictoc}" \
               f"\n\tmrss={self.mrss}" \
               f"\n\toutput_correct={self.output_correct}\n" \
               f"\n\tvalgrind={self.vg}\n" \
               f")"

    def __bool__(self):
        return self.output_correct

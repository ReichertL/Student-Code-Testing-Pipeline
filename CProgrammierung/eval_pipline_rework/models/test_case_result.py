"""
Contains abstractions for the test_case_results
"""
import os

from util.colored_massages import rc, redgreen, ind, errok


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
    short_id = ""
    description = ""
    hint: str = ""
    vg = {}
    ignore: list = []

    def __init__(self, test_case_identifier):
        self.path = test_case_identifier
        self.short_id = test_case_identifier.split(os.path.sep)[-1]

    def append_self(self, description, key):
        update_list = []
        if key in description:
            update_list = description[key]
        if len(self.hint) > 0:
            update_list.append(self.hint)
        else:
            update_list.append(f"bei {self.short_id}")
        description.update({key: update_list})

    def get_failed_description(self, description=None):

        if description is None:
            description = {}
        if not self.timeout:
            self.append_self(description, "timeout")

        if self.timeout and not self.segfault:
            self.append_self(description, "segfault")

        if not self.returncode_correct():
            self.append_self(description, "return_code")

        if self.vg is not None and len(self.vg.keys()) > 0:

            if not self.valgrind_ok:
                if self.vg["invalid_read_count"] > 0:
                    self.append_self(description, "valgrind_read")

                if self.vg["invalid_write_count"] > 0:
                    self.append_self(description, "valgrind_write")

                if self.vg["leak_summary"]["definitely lost"] != (0, 0):
                    self.append_self(description, "valgrind_leak")
                elif self.vg["leak_summary"]['possibly lost'] != (0, 0):
                    self.append_self(description, "valgrind_leak")
                elif self.vg["leak_summary"]['indirectly lost'] != (0, 0):
                    self.append_self(description, "valgrind_leak")
                elif self.vg["leak_summary"]['still reachable'] != (0, 0):
                    self.append_self(description, "valgrind_leak")

        if self.type == "BAD":
            if self.error_msg_quality < 1:
                self.append_self(description, "error_massage")
        else:
            if not self.output_correct and self.timeout:
                self.append_self(description, "output")

        return description

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

    @property
    def valgrind_ok(self):
        if self.vg['ok'] is None:
            return True
        return ((self.vg['ok'] is not False) and
                (self.vg['invalid_read_count'] == 0 and
                 self.vg['invalid_write_count'] == 0))

    def set_passed(self):
        self.return_code = (0 if self.type_good_input else 1)
        self.segfault = True
        self.vg['ok'] = None
        if self.type_good_input:
            self.output_correct = True
        else:
            self.error_msg_quality = 1

    def passed(self):
        res = (self.segfault
               and (self.timeout is not False)
               and self.valgrind_ok
               and self.returncode_correct())
        if self.type_good_input:
            res = res and self.output_correct
        else:
            res = res and (self.error_msg_quality > 0 or
                           'error_msg' in self.ignore or
                           self.output_correct)
        return res

    @property
    def statistics_dict(self):
        return {
            'id': self.short_id,
            'valgrind': rc[None if self.vg['ok'] is None
            else self.valgrind_ok],
            'valgrind_rw': rc[None if self.vg['ok'] is None
            else self.vg['invalid_read_count'] == self.vg['invalid_write_count'] == 0],
            'segfault': rc[self.segfault],
            'timeout': rc[self.timeout],
            'return': redgreen(self.return_code, self.returncode_correct()),
            'err_msg': '---' if 'error_msg' in self.ignore else errok(self.error_msg_quality),
            'error_line': self.error_line[:25].strip(),
            'passed_indicator': ind[bool(self)],
            'description': self.description if len(self.description) else self.short_id,
            'output': rc[self.output_correct],
        }

    def returncode_correct(self):
        return min(self.return_code, 1) == (0 if self.type_good_input else 1)

    def error(self, err):
        if err == 'timeout':
            return not self.timeout
        if err == 'segfault':
            return self.timeout and not self.segfault
        if not (self.segfault and self.timeout):
            return False
        elif err == 'output':
            return not self.output_correct
        elif err == 'vg_leak':
            return 'leak_summary' in self.vg
        elif err == 'vg_read':
            return self.vg['invalid_read_count'] > 0
        elif err == 'vg_write':
            return self.vg['invalid_write_count'] > 0
        elif err == 'err_msg':
            return self.error_msg_quality == 0
        elif err == 'returncode':
            return not self.returncode_correct()
        else:
            raise ValueError('Unknown error type "{}"'.format(err))

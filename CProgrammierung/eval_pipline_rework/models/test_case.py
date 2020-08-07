"""Implements abstraction for TestCase test_case_type"""
import os


class TestCase:
    """Abstraction of TestCase Type consists of configuration input, output, error"""
    path: str = ""
    test_input: str = ""
    test_output: str = ""
    error_expected: bool = False
    valgrind_needed = False
    id = -1
    short_id = ""
    description = ""
    hint = ""
    type = ""
    rlimit = 0

    def __init__(self, path, test_input, test_output, error_expected):
        """
        :param path: base configuration where this testcase is loaded from
        :param test_input: test input
        :param test_output:
        expected output for error testcases this is an empty string
        :param error_expected: indicates whether an error is expected or not.
        """
        self.path = path
        self.short_id = path.split(os.path.sep)[-1]
        self.test_input = test_input
        self.test_output = test_output
        self.error_expected = error_expected

    def __str__(self):
        """
        Returns a string representation of the testcase
        :return: String representation of the testcase

               #f"Input:\n{self.test_input}\n" \
               f"Output:\n{self.test_output}\n" \
        """
        return f"Path: {self.path}\n" \
               f"Error expected: {self.error_expected}\n" \
               f"id: {self.id}\n" \
               f"hint: {self.hint}\n" \
               f"description: {self.description}\n"

    def __eq__(self, other):
        """
        defines quality,
        which is the case if they are loaded from the same source
        """
        if isinstance(self, type(other)):
            return self.path == other.configuration

        return False

    def __ne__(self, other):
        """
        defines inequality,
        which is the case if they are not equal
        """
        return not self.__eq__(other)
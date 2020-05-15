"""Implements abstraction for TestCase type"""


class TestCase:
    """Abstraction of TestCase Type consists of path input, output, error"""
    path: str = ""
    test_input: str = ""
    test_output: str = ""
    error_expected: bool = False

    def __init__(self, path, test_input, test_output, error_expected):
        """
        :param path: base path where this testcase is loaded from
        :param test_input: test input
        :param test_output:
        expected output for error testcases this is an empty string
        :param error_expected: indicates whether an error is expected or not.
        """
        self.path = path
        self.test_input = test_input
        self.test_output = test_output
        self.error_expected = error_expected

    def __str__(self):
        return f"Path: {self.path}\n" \
               f"Input:\n{self.test_input}\n" \
               f"Output:\n{self.test_output}\n" \
               f"Error expected: {self.error_expected}\n"

    def __eq__(self, other):
        """
        defines quality,
        which is the case if they are loaded from the same source
        """
        if isinstance(self.__class__, other):
            return self.path == other.path

        return False

    def __ne__(self, other):
        """
        defines inequality,
        which is the case if they are not equal
        """
        return not self.__eq__(other)

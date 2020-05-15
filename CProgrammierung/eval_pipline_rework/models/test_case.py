class TestCase:
    path: str = ""
    test_input: str = ""
    test_output: str = ""
    error_expected: bool = False

    def __init__(self, path, test_input, test_output, error_expected):
        self.path = path
        self.test_input = test_input
        self.test_output = test_output
        self.error_expected = error_expected

    def __str__(self):
        return f"Path: {self.path}\n" \
               f"Input:\n{self.test_input}\n" \
               f"Output:\n{self.test_output}\n" \
               f"Error expected: {self.error_expected}\n"

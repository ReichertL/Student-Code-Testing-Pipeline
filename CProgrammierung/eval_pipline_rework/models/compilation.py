""" Model Class to model compilation results
"""


class Compilation:
    """Compilation:
    Represents the results of a compilation try
    """
    return_code: int = -128
    commandline: str = ''
    output: str = ''

    def __init__(self, return_code, commandline, output):
        self.return_code = return_code
        self.commandline = commandline
        self.output = output

    def __bool__(self):
        return self.return_code == 0

    def __str__(self):
        return f"return code: {self.return_code}\ncall: {self.commandline}\nerror: {self.output}\n"

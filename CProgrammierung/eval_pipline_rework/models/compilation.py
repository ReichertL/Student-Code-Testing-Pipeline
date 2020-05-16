""" Model Class to model compilation results
"""


class Compilation:
    """Compilation:
    Represents the results of a compilation try
    """
    student_key: int = -1
    submission_key: int = -1
    return_code: int = -128
    commandline: str = ''
    output: str = ''

    def __init__(self,
                 return_code,
                 commandline,
                 output):
        """
        Instantiates a compilation result
        :param return_code: return code of the compiler call
        :param commandline: call
        :param output: out of the compiler
        """

        self.return_code = return_code
        self.commandline = commandline
        self.output = output

    def __bool__(self):
        """
        checks whether the compilation was successful
        :return: True if successful False else
        """
        return self.return_code == 0

    def __str__(self):
        """
        generates a string representation of the compilation try
        :return: String representation
        """
        return f"return code: {self.return_code} " \
               f"call: {self.commandline} " \
               f"error: {self.output}"

    def get_database_entry(self):
        """
        Generates a database entry representation
        :return: database entry representation
        """
        return [self.student_key,
                self.submission_key,
                self.return_code,
                self.commandline,
                self.output]

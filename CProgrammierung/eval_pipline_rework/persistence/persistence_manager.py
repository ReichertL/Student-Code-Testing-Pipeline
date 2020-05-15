"""abstract class too provide an persistence interface"""


class PersistenceManager:
    """abstract class too provide an persistence interface"""

    def __init__(self):
        pass

    def write_student(self, student):
        """

        :param student:
        :return:
        """

    def read_student(self, student_key):
        """

        :param student_key:
        :return:
        """

    def write_submission(self, student_key, submission_key):
        """

        :param submission_key:
        :param student_key:
        :return:
        """

    def read_submission(self, student_key, submission_key):
        """

        :param submission_key:
        :param student_key:
        :return:
        """

    def write_student_list(self, students):
        """

        :param students:
        :return:
        """

    def read_students_list(self, students_keys):
        """

        :param students_keys:
        :return: list of students with respect to the given keys
        """

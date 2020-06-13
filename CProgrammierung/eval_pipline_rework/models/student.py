"""Class which abstracts a student"""


class Student:
    """Class which abstracts a student"""
    name: str = ''
    moodle_id: str = ''
    data_base_key = -1
    submissions = None
    passed = False

    def __init__(self, student_name, student_id, persistence_manager=None, student_key=None):
        """
        :param student_name: full name of the student
        :param student_id: moodle id of the student
        :param persistence_manager
        :param student_key: a given database key
        database manager to set relevant keys
        """
        if persistence_manager is None and student_key is None:
            raise ValueError

        self.name = student_name
        self.moodle_id = student_id
        if student_key is None:
            self.set_database_key(persistence_manager)
        else:
            self.data_base_key = student_key

    def __str__(self):
        submission_representation = ""
        if self.submissions is not None:
            for submission in self.submissions:
                submission_representation = submission_representation + f"\n\t{submission}"
        return f"Student(\ndata_base_key={self.data_base_key}\n" \
               f"name={self.name}\n" \
               f"moodle_id={self.moodle_id}\n" \
               f"passed={self.passed}\n" \
               f"submissions=[{submission_representation}])"

    def get_all_submissions(self, database_manager):
        self.submissions = database_manager.get_submissions_for_student(self)
        return self.submissions

    def earliest_submission(self, database_manager):
        submissions = database_manager.get_submissions_for_student(self)

        if len(submissions) > 0:
            return submissions[0]

        return None

    def latest_submission(self, database_manager):
        submissions = database_manager.get_submissions_for_student(self)

        if len(submissions) > 0:
            return submissions[-1]

        return None

    def set_database_key(self, database_manager):
        """
        aquires a database key which is unique among all students
        :param database_manager: encapsulates the database
        """
        self.data_base_key = database_manager.register_student(self)

    def get_database_entry(self):
        """Generates a database entry for that student"""
        return [self.data_base_key, self.moodle_id, self.name]

    def passed_assignment(self):
        self.passed = True

    def get_unchecked_submissions(self):
        return [i for i in self.submissions if i.is_checked is False]

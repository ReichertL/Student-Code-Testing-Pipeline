"""Class which abstracts a student"""


class Student:
    """Class which abstracts a student"""
    name: str = ''
    moodle_id: str = ''
    data_base_key = -1

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
        return f"{self.data_base_key} {self.name} {self.moodle_id}"

    def set_database_key(self, database_manager):
        """
        aquires a database key which is unique among all students
        :param database_manager: encapsulates the database
        """
        self.data_base_key = database_manager.register_student(self)

    def get_database_entry(self):
        """Generates a database entry for that student"""
        return [self.data_base_key, self.moodle_id, self.name]

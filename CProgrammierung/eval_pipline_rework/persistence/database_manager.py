"""
    implements PersistenceManager
    in this case, SQLite database
"""
import sqlite3

from persistence.persistence_manager import PersistenceManager


class SQLiteDatabaseManager(PersistenceManager):
    """
    implements PersistenceManager

    """
    database = None

    def __init__(self):
        super().__init__()
        self.database = sqlite3.connect("test.db")
        print("implementation of persistence manager")

    def create(self):
        cursor = self.database.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS students
            (student_name, student_id, submission_id)''', )
        self.create_submission_table(cursor)
        self.create_test_case_table(cursor)

        self.database.commit()

    def insert_student(self, student):
        self.database.cursor().execute('''INSERT INTO students VALUES (?,?,?)''', (student.name, student.id_,
                                                                                   student.submission_id))
        self.database.commit()

    def close(self):
        self.database.cursor().execute('''DELETE FROM students;''')
        self.database.commit()
        self.database.close()

    def create_submission_table(self, cursor):
        cursor.execute('''CREATE TABLE IF NOT EXISTS submissions
                    (    timestamp,mtime,tests_bad_input,tests_good_input, tests_performance,compilation,fast,timing)''', )

    @staticmethod
    def create_test_case_table(cursor):
        cursor.execute('''CREATE TABLE IF NOT EXISTS test_results
                   (testcase_id, 
                   vg_info, 
                   ignore,
                   type_good_input,
                   signal,
                   segfault,
                   timeout,
                   cpu_time,
                   real_time,
                   tictoc,
                   mrss,
                   return_code,
                   output_correct,
                   errormsg_quality,
                   error_line)''', )

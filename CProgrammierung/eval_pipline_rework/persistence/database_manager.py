"""
    implements PersistenceManager
    in this case, SQLite database
"""
import sqlite3
from datetime import datetime

from models.compilation import Compilation
from models.student import Student
from models.submission import Submission
from models.test_case_result import TestCaseResult
from persistence.persistence_manager import PersistenceManager


class SQLiteDatabaseManager(PersistenceManager):
    """
    implements PersistenceManager

    """
    database = None

    def __init__(self):
        super().__init__()
        self.database = sqlite3.connect("./resources/test.db")

    def get_test_case_result(self, student, submission):
        """
        Retrieves all test case results
        for a specific submission of the student.
        If it returns an empty list,
        it's likely that the submission didn't compile.
        :param student: The author of the submission
        :param submission: The respective submission
        :return: All test_case_results
        available for this Submission
        """
        student_key = self.get_student_key(student)
        submission_key = self.get_submission_key(student, submission)
        cursor = self.database.cursor()
        cursor.execute("""SELECT * FROM test_results
            WHERE student_key=? AND submission_key=?
        """, [student_key, submission_key])
        raw_results = cursor.fetchall()
        results = [TestCaseResult(raw_test_case_result[2])
                   for raw_test_case_result in raw_results]
        for test_case_result in results:
            test_case_result.student_key = student_key
            test_case_result.submission_key = submission_key
        return results

    def insert_test_case_result(self, student, submission, test_case_result):
        """
        Inserts a test_case for a specific student and submission
        into the database
        :param student: The author of the submission
        :param submission:
        The submission which pruduced this test_case_result
        :param test_case_result: The results of the test_case
        :return:
        """

        student_key = self.get_student_key(student)
        submission_key = self.get_submission_key(student, submission)
        cursor = self.database.cursor()

        cursor.execute("""SELECT * FROM test_results
                            WHERE student_key=?
                                    AND submission_key=? """,
                       [student_key,
                        submission_key])
        results = cursor.fetchall()
        already_in = False
        for i in results:
            if test_case_result.path == i[2]:
                already_in = True
        if not already_in:
            cursor.execute("""INSERT INTO test_results VALUES (?,?,?)
            """,
                           [
                               student_key,
                               submission_key,
                               test_case_result.path
                           ])
        else:
            cursor.execute("""UPDATE test_results SET path=?
            WHERE student_key=? AND submission_key=? AND path=?
            """,
                           [
                               test_case_result.path,
                               student_key,
                               submission_key,
                               test_case_result.path
                           ])

        self.database.commit()

    def get_compilation_result(self, student, submission):
        """
        Retrieves the compilation results for a specific submission
        of a specific student
        :param student: the student who is the author of the submission
        :param submission: the submission
        whose compilation results shall be retrieved
        :return: a compilation result
        """
        student_key = self.get_student_key(student)
        submission_key = self.get_submission_key(student, submission)
        cursor = self.database.cursor()
        raw_results = cursor.execute(
            """SELECT * FROM compilations
             WHERE student_key=? AND submission_key=?""",
            [student_key, submission_key]).fetchall()

        if len(raw_results) != 1:
            raise ValueError("Compilation not found!")
        result = Compilation(raw_results[0][2],
                             raw_results[0][3],
                             raw_results[0][4])
        result.student_key = raw_results[0][0]
        result.submission_key = raw_results[0][1]
        self.database.commit()
        return result

    def insert_compilation_result(self, student, submission, compilation):
        """
        Inserts a compilation result for a submission
        for a student into the database
        If already there is already a compilation for this submission
        it gets updated
        :param student: the students who is the author of the submission
        :param submission: the submission which was compiled
        :param compilation: the result of the compilation
        :return: nothing,
        sets student_key and submission_key for the compilation
        """
        student_key = self.get_student_key(student)
        submission_key = self.get_submission_key(student, submission)
        cursor = self.database.cursor()

        cursor.execute("""SELECT * FROM compilations
                        WHERE student_key=? 
                        AND submission_key=?""",
                       [student_key, submission_key])

        if len(cursor.fetchall()) == 0:
            cursor.execute("""INSERT INTO compilations VALUES (?,?,?,?,?)""",
                           [
                               student_key,
                               submission_key,
                               compilation.return_code,
                               compilation.commandline,
                               compilation.output
                           ])
        else:
            cursor.execute("""UPDATE compilations
            SET return_code=?, commandline=?,compiler_output =? 
            WHERE student_key=? AND submission_key=?
            """,
                           [
                               compilation.return_code,
                               compilation.commandline,
                               compilation.output,
                               student_key,
                               submission_key
                           ])
        compilation.student_key = student_key
        compilation.submission_key = submission_key
        self.database.commit()

    def insert_submission(self, student, submission):
        """
        inserts a submission for a student if absent
        :param student: the assignee which uploaded the submission
        :param submission: the respective submission
        :return: nothing
        """
        cursor = self.database.cursor()
        cursor.execute(
            """SELECT * FROM submissions
                WHERE student_key =? AND submission_key=?"""
            , [submission.student_key, submission.submission_key]
        )
        is_already_in = cursor.fetchone()
        if is_already_in is not None and len(is_already_in) > 0:
            return
        key = student.data_base_key
        if key < 0:
            key = self.get_student_by_name(student.name).data_base_key

        submission.student_key = key

        cursor.execute(
            """SELECT * FROM submissions
                WHERE student_key =?"""
            , [submission.student_key]
        )
        results = cursor.fetchall()
        submission.submission_key = len(results)
        cursor.execute("""INSERT INTO submissions VALUES (?,?,?)""",
                       [submission.student_key,
                        submission.submission_key, datetime.now()])

        self.database.commit()

    def get_submissions_for_student(self, student):
        """
        retrieves all submissions of a student
        :param student: the assignee whose submissions are wanted
        :return: all submissions of the respective student
        as submission object list
        """
        cursor = self.database.cursor()
        key = self.get_student_key(student)
        cursor.execute(
            """SELECT * FROM submissions
                WHERE student_key =?"""
            , [key]
        )
        results = cursor.fetchall()
        submissions = []

        for result in results:
            submission = Submission()
            submission.student_key = result[0]
            submission.submission_key = result[1]
            submission.timestamp = datetime.fromisoformat(result[2])

            submissions.append(submission)
        return submissions

    def register_student(self, student):
        """Try to register a new student.
        Returns old student key if this student already exists
        @:param student student to register
        @:return student key which is a unique identifier
        """
        if student.data_base_key > -1:
            return student.data_base_key

        cursor = self.database.cursor()
        cursor.execute(
            """SELECT * FROM students
                WHERE student_name =?
                AND student_moodle_id=?"""
            , [student.name, student.moodle_id]
        )
        rows = cursor.fetchall()
        if len(rows) > 1:
            raise Exception("More than one student with this id and name!")
        if len(rows) == 1:
            return rows[0][0]

        new_student_id = len(cursor.execute(
            """SELECT * FROM students"""
        )
                             .fetchall())
        cursor.execute("""INSERT INTO students VALUES (?,?,?)""",
                       [new_student_id,
                        student.name,
                        student.moodle_id])

        self.database.commit()
        return new_student_id

    def get_student_by_key(self, key):
        """
        retrieves a student by its database key
        :param key: database key
        :return: student
        """
        cursor = self.database.cursor()
        cursor.execute(
            """SELECT * FROM students
                WHERE student_key=?"""
            , [int(key)]
        )

        students = cursor.fetchall()
        if len(students) != 1:
            raise ValueError

        retrieved_students = Student(
            students[0][1],
            students[0][2],
            student_key=students[0][0])
        return retrieved_students

    def get_student_by_name(self, name):
        """
        retrieves a student by its name
        :param name full name of the student
        :return: students
        """
        cursor = self.database.cursor()
        cursor.execute(
            """SELECT * FROM students
                WHERE student_name=?"""
            , [str(name)]
        )
        students = cursor.fetchall()
        if len(students) != 1:
            raise ValueError

        retrieved_students = Student(
            students[0][1],
            students[0][2],
            student_key=students[0][0])
        return retrieved_students

    def get_student_by_moodle_id(self, moodle_id):
        """
        retrieves a student by its moodle id
        :param moodle_id of the student
        :return: students
        """
        cursor = self.database.cursor()
        cursor.execute(
            """SELECT * FROM students
                WHERE student_moodle_id=?"""
            , [str(moodle_id)]
        )

        students = cursor.fetchall()

        if len(students) != 1:
            raise ValueError

        retrieved_students = Student(
            students[0][1],
            students[0][2],
            student_key=students[0][0])
        return retrieved_students

    def get_student_key(self, student):
        """
        given a student retrieves its database key
        :param student: the respective student
        :return: the students database key
        """
        student_key = student.data_base_key

        if student_key < 0:
            student_key_name = self.get_student_by_name(student.name) \
                .data_base_key
            student_key_id = self.get_student_by_moodle_id(student.moodle_id) \
                .data_base_key
            student_key = max(student_key_id, student_key_name)

        if student_key < 0:
            raise ValueError("Student not found!")

        return student_key

    def get_submission_key(self, student, submission):
        """
        Given a student and a submission returns the submission key
        :param student: the student to whom the submission belong
        :param submission: the respective submission
        :return: the submission_key
        """
        submission_key = submission.submission_key
        if submission_key < 0:
            self.insert_submission(student, submission)

        submission_key = submission.submission_key
        return submission_key

    def create(self):
        """
         calls create methods
         creats all needed tables if nescessary
        :return: nothing
        """
        cursor = self.database.cursor()
        self.create_student_table(cursor)
        self.create_submission_table(cursor)
        self.create_test_case_table(cursor)
        self.create_compilation_table(cursor)
        self.database.commit()

    def close(self):
        """
        commits all changes and closes the database connection
        :return: nothing
        """
        self.database.commit()
        self.database.close()

    @staticmethod
    def create_student_table(cursor):
        """
        creats the new student table if it doesn't exist
        :param cursor: pointer to the database
        :return: nothing
        """
        cursor.execute('''CREATE TABLE IF NOT EXISTS students
            (student_key  INTEGER ,
            student_name TEXT NOT NULL ,  
           student_moodle_id INTEGER)''')

    @staticmethod
    def create_submission_table(cursor):
        """
        creats the new submission table if it doesn't exist
        :param cursor: pointer to the database
        :return: nothing
        """
        cursor.execute('''CREATE TABLE IF NOT EXISTS submissions
                    (student_key  INTEGER ,
                    submission_key  INTEGER,
                    submission_timestamp TIMESTAMP 
                    )''')

    # ,
    # timestamp,
    # mtime,
    # tests_bad_input,
    # tests_good_input,
    # tests_performance,
    # compilation,
    # fast,
    # timing

    @staticmethod
    def create_test_case_table(cursor):
        """
        creats the new test_case_result table if it doesn't exist
        :param cursor: pointer to the database
        :return: nothing
        """
        cursor.execute('''CREATE TABLE IF NOT EXISTS test_results
                   (
                   student_key INTEGER ,
                   submission_key INTEGER,
                   path TEXT NOT NULL
                   )''')
        # testcase_id,
        # vg_info,
        # ignore,
        # type_good_input,
        # signal,
        # segfault,
        # timeout,
        # cpu_time,
        # real_time,
        # tictoc,
        # mrss,
        # return_code,
        # output_correct,
        # errormsg_quality,
        # error_line

    @staticmethod
    def create_compilation_table(cursor):
        """
        creats the new compilation table if it doesn't exist
        :param cursor: pointer to the database
        :return: nothing
        """
        cursor.execute('''CREATE TABLE IF NOT EXISTS compilations
                           (
                           student_key INTEGER ,
                           submission_key INTEGER,
                           return_code INTEGER,
                           commandline TEXT NOT NULL,
                           compiler_output TEXT NOT NULL                           
                           )''')
        # testcase_id,
        # vg_info,
        # ignore,
        # type_good_input,
        # signal,
        # segfault,
        # timeout,
        # cpu_time,
        # real_time,
        # tictoc,
        # mrss,
        # return_code,
        # output_correct,
        # errormsg_quality,
        # error_line

"""
    implements PersistenceManager
    in this case, SQLite database
"""
import sqlite3
import sys
from datetime import datetime
from os.path import getmtime

from models.compilation import Compilation
from models.mail_information import MailInformation
from models.student import Student
from models.submission import Submission
from models.test_case import TestCase
from models.test_case_result import TestCaseResult
from util.absolute_path_resolver import resolve_absolute_path
from util.config_reader import ConfigReader


class SQLiteDatabaseManager:
    """
    implements PersistenceManager

    """
    database = None

    def __init__(self):
        super().__init__()

        p = resolve_absolute_path("/resources/config_database_manager.config")
        configuration = ConfigReader().read_file(str(p))
        self.database = sqlite3.connect(configuration["DATABASE_PATH"])

    def is_empty(self):
        cursor = self.database.cursor()
        cursor.execute("""SELECT * FROM students""")
        results = cursor.fetchone()
        return results is None or len(results) <= 0

    def insert_test_case_information(self, test_case):
        cursor = self.database.cursor()

        cursor.execute("""SELECT * FROM test_cases WHERE test_case_id=?""",
                       [test_case.id])
        result = cursor.fetchall()
        if result is None or len(result) == 0:
            cursor.execute("""INSERT INTO test_cases VALUES (?,?,?,?,?,?,?,?,?,?)
             """, [test_case.id,
                   test_case.path,
                   test_case.test_input,
                   test_case.test_output,
                   1 if test_case.error_expected else 0,
                   1 if test_case.valgrind_needed else 0,
                   test_case.short_id,
                   test_case.description,
                   test_case.hint,
                   test_case.type,
                   ])

        else:
            pass

        self.database.commit()

    def get_test_case_by_id(self, id):
        cursor = self.database.cursor()

        cursor.execute("""SELECT * FROM test_cases WHERE test_case_id=?""",
                       [id])
        raw_result = cursor.fetchall()
        raw_result = raw_result[0]
        test_case = TestCase(raw_result[1], raw_result[2], raw_result[3], raw_result[4] == 1)
        test_case.id = id
        test_case.valgrind_needed = raw_result[5] == 1
        test_case.short_id = raw_result[6]
        test_case.description = raw_result[7]
        test_case.hint = raw_result[8]
        test_case.type = raw_result[9]

        return test_case

    def insert_mail_information(self, student, submission, text):
        cursor = self.database.cursor()
        student_key = student.data_base_key
        submission_key = submission.submission_key

        cursor.execute("""SELECT * FROM mail_log WHERE student_key=? AND submission_key=?""",
                       [student_key, submission_key])
        result = cursor.fetchall()
        if result is None or len(result) == 0:
            cursor.execute("""INSERT INTO mail_log VALUES (?,?,?,?)
            """, [student_key, submission_key, datetime.now(), text])

        else:
            cursor.execute("""UPDATE mail_log
                       SET 
                       last_mailed=?,
                       massage=?
                       WHERE student_key=? AND submission_key=?
                       """, [datetime.now(), text, student_key, submission_key])

        self.database.commit()

    def get_all_mail_information(self, student):
        submissions = self.get_submissions_for_student(student)
        mail_infos = []
        for submission in submissions:
            mail_info = self.get_mail_information(student, submission)
            if mail_info is not None:
                mail_infos.append(mail_info)

        return mail_infos

    def get_mail_information(self, student, submission):
        cursor = self.database.cursor()
        student_key = student.data_base_key
        submission_key = submission.submission_key
        cursor.execute("""SELECT * FROM mail_log WHERE student_key=? AND submission_key=?""",
                       [student_key, submission_key])
        result = cursor.fetchall()
        if result is None or len(result) != 1:
            return None
        else:
            return MailInformation(result)

    def insert_valgrind_result(self, student_key, submission_key, test_case_result):
        vg = test_case_result.vg
        ok = 1 if vg["ok"] else 0
        ok = 2 if vg["ok"] is None else ok
        invalid_read_count = vg["invalid_read_count"] if "invalid_read_count" in vg.keys() else 0
        invalid_write_count = vg["invalid_write_count"] if "invalid_write_count" in vg.keys() else 0
        in_use_at_exit = vg["in_use_at_exit"] if "in_use_at_exit" in vg.keys() else (0, 0)
        total_heap_usage = vg["total_heap_usage"] if "total_heap_usage" in vg.keys() else (0, 0, 0)
        leak_summary = vg["leak_summary"] if "leak_summary" in vg.keys() else {'definitely lost': (0, 0),
                                                                               'indirectly lost': (0, 0),
                                                                               'possibly lost': (0, 0),
                                                                               'still reachable': (0, 0),
                                                                               'suppressed': (0, 0)}
        definitely_lost = leak_summary["definitely lost"]
        indirectly_lost = leak_summary["indirectly lost"]
        possibly_lost = leak_summary["possibly lost"]
        still_reachable = leak_summary["still reachable"]
        suppressed = leak_summary["suppressed"]
        error_summary = vg["error_summary"] if "error_summary" in vg.keys() else (0, 0, 0, 0)

        test_id = test_case_result.id
        cursor = self.database.cursor()
        cursor.execute("""SELECT * FROM valgrind WHERE student_key=? AND submission_key=? AND test_id=?""",
                       [student_key, submission_key, test_id])
        result = cursor.fetchall()
        if result is None or len(result) == 0:
            cursor.execute("""INSERT INTO valgrind VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
                           [
                               student_key,
                               submission_key,
                               test_id,
                               ok,
                               invalid_read_count,
                               invalid_write_count,
                               in_use_at_exit[0],
                               in_use_at_exit[1],
                               total_heap_usage[0],
                               total_heap_usage[1],
                               total_heap_usage[2],
                               definitely_lost[0],
                               definitely_lost[1],
                               indirectly_lost[0],
                               indirectly_lost[1],
                               possibly_lost[0],
                               possibly_lost[1],
                               still_reachable[0],
                               still_reachable[1],
                               suppressed[0],
                               suppressed[1],
                               error_summary[0],
                               error_summary[1],
                               error_summary[2],
                               error_summary[3],

                           ])
        else:
            cursor.execute("""UPDATE valgrind
            SET ok=?,
            invalid_read_count=?,
            invalid_write_count=?,
            in_use_at_exit_bytes=?,
            in_use_at_exit_blocks=?,
            total_heap_usage_allocs=?,
            total_heap_usage_frees=?,
            total_heap_usage_bytes=?,
            definitely_lost_bytes=?,
            definitely_lost_blocks=?,
            indirectly_lost_bytes=?,
            indirectly_lost_blocks=?,
            possibly_lost_bytes=?,
            possibly_lost_blocks=?,
            still_reachable_bytes=?,
            still_reachable_blocks=?,
            suppressed_bytes=?,
            suppressed_blocks=?,
            summary_errors=?,
            summary_contexts=?,
            summary_suppressed_bytes=?,
            summary_suppressed_blocks=?
            WHERE student_key=? AND submission_key=? AND test_id=?
            """, [

                ok,
                invalid_read_count,
                invalid_write_count,
                in_use_at_exit[0],
                in_use_at_exit[1],
                total_heap_usage[0],
                total_heap_usage[1],
                total_heap_usage[2],
                definitely_lost[0],
                definitely_lost[1],
                indirectly_lost[0],
                indirectly_lost[1],
                possibly_lost[0],
                possibly_lost[1],
                still_reachable[0],
                still_reachable[1],
                suppressed[0],
                suppressed[1],
                error_summary[0],
                error_summary[1],
                error_summary[2],
                error_summary[3],
                student_key,
                submission_key,
                test_id

            ])

    def get_valgrind_result(self, student_key, submission_key, test_id):
        vg = {}
        cursor = self.database.cursor()
        cursor.execute("""SELECT * FROM valgrind WHERE student_key=? AND submission_key=? AND test_id=?""",
                       [student_key, submission_key, test_id])
        result = cursor.fetchall()
        if result is not None and len(result) > 0:
            raw_result = result[0]
        else:
            return None
        ok = vg.update({"ok": (False, True, None)[raw_result[3]]})
        vg.update({"invalid_read_count": raw_result[4]})
        vg.update({"invalid_write_count": raw_result[5]})
        vg.update({"in_use_at_exit": (raw_result[6], raw_result[7])})
        vg.update({"total_heap_usage": (raw_result[8], raw_result[9], raw_result[10])})
        leak_summary = {'definitely lost': (raw_result[11], raw_result[12]),
                        'indirectly lost': (raw_result[13], raw_result[14]),
                        'possibly lost': (raw_result[15], raw_result[16]),
                        'still reachable': (raw_result[17], raw_result[18]),
                        'suppressed': (raw_result[19], raw_result[20])}

        vg.update({"leak_summary": leak_summary})
        vg.update({"error_summary": (raw_result[21], raw_result[22], raw_result[23], raw_result[24])})

        return vg

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
        results = []

        for result in raw_results:
            test_case_result = TestCaseResult(result[4])
            test_case_result.student_key = student_key
            test_case_result.submission_key = submission_key
            test_case_result.id = result[2]
            test_case_result.type = result[3]
            test_case_result.error_line = result[5]
            test_case_result.error_msg_quality = result[6]
            test_case_result.output_correct = result[7]
            test_case_result.return_code = result[8]
            test_case_result.type_good_input = result[9]
            test_case_result.signal = result[10]
            test_case_result.segfault = result[11]
            test_case_result.timeout = result[12]
            test_case_result.cpu_time = result[13]
            test_case_result.realtime = result[14]
            test_case_result.tictoc = result[15]
            test_case_result.mrss = result[16]
            test_case_result.vg = self.get_valgrind_result(student_key, submission_key, test_case_result.id)
            test_case = self.get_test_case_by_id(test_case_result.id)
            test_case_result.hint = test_case.hint
            test_case_result.description = test_case.description if len(
                test_case.description) > 0 else test_case.short_id
            results.append(test_case_result)
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
        test_id = test_case_result.id
        cursor = self.database.cursor()

        cursor.execute("""SELECT * FROM test_results
                            WHERE student_key=?
                                    AND submission_key=? AND test_id=?""",
                       [student_key,
                        submission_key, test_id])
        results = cursor.fetchall()
        already_in = False
        for i in results:
            if test_case_result.path == i[4] and student_key == i[0] and submission_key == i[1]:
                already_in = True
        if not already_in:
            cursor.execute("""INSERT INTO test_results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
                           [
                               student_key,
                               submission_key,
                               test_id,
                               test_case_result.type,
                               test_case_result.path,
                               test_case_result.error_line,
                               test_case_result.error_msg_quality,
                               test_case_result.output_correct,
                               test_case_result.return_code,
                               test_case_result.type_good_input,
                               test_case_result.signal,
                               test_case_result.segfault,
                               test_case_result.timeout,
                               test_case_result.cpu_time,
                               test_case_result.realtime,
                               test_case_result.tictoc,
                               test_case_result.mrss
                           ])
        else:
            cursor.execute("""UPDATE test_results
            SET test_type=?,
            path=?,
            error_line=?,
            error_quality=?,
            output_correct=?,
            return_code=?,
            good_input=?,
            signal=?,
            segfault=?,
            timeout=?,
            cpu_time=?,
            real_time=?,
            tictoc=?,
            mrss=?
            WHERE student_key=? AND submission_key=? AND test_id=?
            """,
                           [
                               test_case_result.type,
                               test_case_result.path,
                               test_case_result.error_line,
                               test_case_result.error_msg_quality,
                               test_case_result.output_correct,
                               test_case_result.return_code,
                               test_case_result.type_good_input,
                               test_case_result.signal,
                               test_case_result.segfault,
                               test_case_result.timeout,
                               test_case_result.cpu_time,
                               test_case_result.realtime,
                               test_case_result.tictoc,
                               test_case_result.mrss,
                               student_key,
                               submission_key,
                               test_id
                           ])

        self.insert_valgrind_result(student_key, submission_key, test_case_result)
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
            return None
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
        submission.mtime = int(getmtime(submission.path))
        cursor = self.database.cursor()
        cursor.execute(
            """SELECT * FROM submissions
                WHERE student_key =?"""
            , [student.data_base_key]
        )
        submissions = cursor.fetchall()
        is_already_in = False
        for current_submission in submissions:
            if current_submission[3] == submission.path:
                is_already_in = True
        if is_already_in:
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
        cursor.execute("""INSERT INTO submissions VALUES (?,?,?,?,?,?,?,?)""",
                       [submission.student_key,
                        submission.submission_key,
                        datetime.utcfromtimestamp(int(submission.mtime)).strftime("%Y-%m-%d %H:%M:%S"),
                        submission.path,
                        (1 if submission.is_checked else 0),
                        (1 if submission.fast else 0),
                        submission.mtime,
                        (1 if submission.passed else 0),
                        ])
        compilation_result = submission.compilation
        if compilation_result is not None:
            self.insert_compilation_result(student, submission, compilation_result)

        self.database.commit()

    def set_submission_checked(self, submission):
        cursor = self.database.cursor()
        cursor.execute(
            """SELECT * FROM submissions
                WHERE student_key =? AND submission_key=?"""
            , [submission.student_key, submission.submission_key]
        )
        is_already_in = cursor.fetchone()
        if is_already_in is not None and len(is_already_in) > 0:
            cursor.execute("""UPDATE submissions SET submission_is_checked=?, submission_passed=?
                        WHERE student_key=? AND submission_key=?
                        """,
                           [
                               1 if submission.is_checked else 0,
                               1 if submission.passed else 0,
                               submission.student_key,
                               submission.submission_key,

                           ])
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
            submission.timestamp = datetime.utcfromtimestamp(int(result[6])).strftime("%Y-%m-%d %H:%M:%S")
            submission.path = result[3]
            submission.is_checked = False if result[4] == 0 else True
            submission.fast = False if result[5] == 0 else True
            submission.mtime = result[6]
            submission.compilation = self.get_compilation_result(student, submission)
            submission.fast = False if result[7] == 0 else True
            test_case_results = self.get_test_case_result(student, submission)
            submission.tests_good_input = []
            submission.tests_bad_input = []
            submission.tests_extra_input = []
            for test_case_result in test_case_results:
                if test_case_result.type == "BAD":
                    submission.tests_bad_input.append(test_case_result)
                if test_case_result.type == "GOOD":
                    submission.tests_good_input.append(test_case_result)
                if test_case_result.type == "EXTRA":
                    submission.tests_extra_input.append(test_case_result)

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
        cursor.execute("""INSERT INTO students VALUES (?,?,?,?)""",
                       [new_student_id,
                        student.name,
                        student.moodle_id, student.passed])

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
        retrieved_students.passed = students[0][3] == 1
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
        if len(students) < 1:
            print(f"----found no student with name: {name}----")
            return
        if len(students) > 1:
            print(f"----found more than one student with name: {name}----\n{students}")

        retrieved_students = Student(
            students[0][1],
            students[0][2],
            student_key=students[0][0])
        retrieved_students.passed = students[0][3] == 1
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
        retrieved_students.passed = students[0][3] == 1
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

    def set_student_passed(self, student):
        cursor = self.database.cursor()
        cursor.execute(
            """SELECT * FROM students
                WHERE student_key =?"""
            , [student.data_base_key]
        )
        is_already_in = cursor.fetchone()
        if is_already_in is not None and len(is_already_in) > 0:
            cursor.execute("""UPDATE students SET student_passed=?
                        WHERE student_key=?
                        """,
                           [
                               1 if student.passed else 0,
                               student.data_base_key,
                           ])
        self.database.commit()

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

    def get_all_students(self):
        """
        Retrieves all students from the database
        :return: List of all students
        """
        cursor = self.database.cursor()
        cursor.execute("""SELECT * FROM students""")
        raw_students = cursor.fetchall()
        parsed_students = []
        for raw_student in raw_students:
            parsed_student = Student(raw_student[1],
                                     raw_student[2],
                                     student_key=raw_student[0])
            parsed_student.passed = raw_student[3] == 1
            parsed_students.append(parsed_student)
        return parsed_students

    def create(self):
        """
         calls create methods
         creats all needed tables if nescessary
        :return: nothing
        """
        cursor = self.database.cursor()
        self.create_student_table(cursor)
        self.create_submission_table(cursor)
        self.create_test_case_results_table(cursor)
        self.create_compilation_table(cursor)
        self.create_valgrind_table(cursor)
        self.create_mail_log(cursor)
        self.create_test_case_table(cursor)
        self.create_abtestat_table(cursor)
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
           student_moodle_id INTEGER,
           student_passed INTEGER)''')

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
                    submission_timestamp TIMESTAMP,
                    submission_path TEXT NOT NULL,
                    submission_is_checked INTEGER,
                    submission_fast INTEGER,
                    submission_mtime INTEGER,
                    submission_passed INTEGER                    
                    )''')

    @staticmethod
    def create_test_case_results_table(cursor):
        """
        creats the new test_case_result table if it doesn't exist
        :param cursor: pointer to the database
        :return: nothing
        """

        cursor.execute('''CREATE TABLE IF NOT EXISTS test_results
                   (
                   student_key INTEGER ,
                   submission_key INTEGER,
                   test_id INTEGER ,
                   test_type TEXT NOT NULL,
                   path TEXT NOT NULL,
                   error_line TEXT NOT NULL,
                   error_quality INTEGER,
                   output_correct INTEGER,
                   return_code INTEGER,
                   good_input INTEGER,
                   signal INTEGER,
                   segfault INTEGER,
                   timeout INTEGER,
                   cpu_time REAL,
                   real_time REAL,
                   tictoc REAL,
                   mrss INTEGER
                   
                   )''')

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

    @staticmethod
    def create_valgrind_table(cursor):

        cursor.execute('''CREATE TABLE IF NOT EXISTS valgrind
                           (
                           student_key INTEGER ,
                           submission_key INTEGER,
                           test_id INTEGER,
                           ok INTEGER,
                           invalid_read_count INTEGER ,
                           invalid_write_count INTEGER,
                           in_use_at_exit_bytes INTEGER,
                           in_use_at_exit_blocks INTEGER,
                           total_heap_usage_allocs INTEGER,
                           total_heap_usage_frees INTEGER,
                           total_heap_usage_bytes INTEGER,
                           definitely_lost_bytes INTEGER,
                           definitely_lost_blocks INTEGER,
                           indirectly_lost_bytes INTEGER,                           
                           indirectly_lost_blocks INTEGER,
                           possibly_lost_bytes INTEGER,                           
                           possibly_lost_blocks INTEGER,                        
                           still_reachable_bytes INTEGER,
                           still_reachable_blocks INTEGER,
                           suppressed_bytes INTEGER,
                           suppressed_blocks INTEGER,
                           summary_errors INTEGER ,                                                     
                           summary_contexts INTEGER ,                                                     
                           summary_suppressed_bytes INTEGER ,                                                     
                           summary_suppressed_blocks INTEGER                                                
                           )''')

    @staticmethod
    def create_mail_log(cursor):

        cursor.execute('''CREATE TABLE IF NOT EXISTS mail_log
                           (student_key INTEGER,
                           submission_key INTEGER,
                           last_mailed TIMESTAMP,
                           massage TEXT NOT NULL                                            
                           )''')

    @staticmethod
    def create_test_case_table(cursor):
        cursor.execute('''CREATE TABLE IF NOT EXISTS test_cases
                           (test_case_id INTEGER,
                           path TEXT NOT NULL ,
                           input TEXT NOT NULL ,
                           output TEXT NOT NULL, 
                           error_expected INTEGER ,
                           valgrind_needed INTEGER ,
                           short_id TEXT NOT NULL,                                            
                           description TEXT NOT NULL,                                            
                           hint TEXT NOT NULL ,                                           
                           type TEXT NOT NULL                                            
                           )''')

    def is_student_done(self, student):
        student_key = self.get_student_key(student)
        cursor = self.database.cursor()
        cursor.execute(
            """SELECT * FROM abtestat_done
                WHERE student_key=?"""
            , [student_key]
        )
        raw_result = cursor.fetchall()

        return len(raw_result) > 0

    def get_testat_information(self):
        cursor = self.database.cursor()
        cursor.execute(
            """SELECT * FROM abtestat_done"""
        )
        return cursor.fetchall()

    def revert_abtestat(self, student):
        student_key = self.get_student_key(student)

        print(f"Should {student.name} also marked as not passed the test cases?")
        if 'y' == sys.stdin.readline()[:1]:
            student.passed = False
            self.set_student_passed(student)

        cursor = self.database.cursor()
        cursor.execute(
            """SELECT * FROM abtestat_done
                WHERE student_key=?"""
            , [student_key]
        )
        raw_result = cursor.fetchall()
        if len(raw_result) > 0:
            cursor.execute(""" DELETE FROM abtestat_done WHERE student_key=?""", [student_key])
        self.database.commit()

    def mark_as_done(self, student):
        student_key = self.get_student_key(student)
        if not student.passed:
            print(f"{student.name} has not passed so far, mark abtestat as done anyways?")
            if 'y' != sys.stdin.readline()[:1]:
                return
            else:
                student.passed = True
                self.set_student_passed(student)
        cursor = self.database.cursor()
        cursor.execute(
            """SELECT * FROM abtestat_done
                WHERE student_key=?"""
            , [student_key]
        )
        raw_result = cursor.fetchall()
        if len(raw_result) == 0:
            cursor.execute(""" INSERT INTO abtestat_done VALUES (?,?,?,?)""",
                           [student_key, student.moodle_id, datetime.now(), 1])
        self.database.commit()

    @staticmethod
    def create_abtestat_table(cursor):
        cursor.execute('''CREATE TABLE IF NOT EXISTS abtestat_done
                               (student_key INTEGER,
                               moodle_id INTEGER ,
                               time_stamp TIMESTAMP,
                               done INTEGER                                        
                               )''')

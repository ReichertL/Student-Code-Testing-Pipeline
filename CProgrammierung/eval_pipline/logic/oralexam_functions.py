"""
This class deals with handling and recording oral exams. This functionality does not have to be used.
"""

from datetime import datetime
import sys
import database.database_manager as dbm
from database.students import Student
from util.select_option import select_option_interactive
from moodle.moodle_reporter import MoodleReporter


class OralExamFunctions:

    def __init__(self, args):
        """
        Constructor creates a MoodleReporter instance
        based on given arguments which determine the behaviour

        Parameters;
            given commandline arguments (ArgumentParser object)
        """
        self.args=args

    def oralexam_mark_as_done(self, names):
        """
        This function stores in the database that a given student passed the oral exam.
        If the student has not submitted a submission yet which passed the testcases, the user is promoted to confirm the desicion.
        Then the user is promoted to provide the student's University ID (german: Matrikel number).
        Only integers are accepted here.

        Parameters:
            names (list of string): List of student names

        Returns:  Nothing
        """

        for name in names:
            student=Student.get_student_by_name(name)
            if type(student)==list:
                student=select_option_interactive(student)
            if not Student.is_student_passed(student.name):
                print(f"{student.name} has not passed so far, mark oral exam as done anyways?(y/n)")
                if 'y'!=sys.stdin.readline()[:1]:
                    return

            print(f"Please insert the students University identification number or Matrikel number!")
            answer_accepted=False
            uni_id=0
            while not answer_accepted:
                uni_id=sys.stdin.readline()
                try:
                    uni_id=int(uni_id)
                    answer_accepted=True
                except ValueError:
                    print(f"{uni_id} is not a number, please select again!")

            student.grade=2
            student.uni_id=uni_id
            student.oralexam_time=datetime.now()
            reporter=MoodleReporter(self.args)
            reporter.update_grade_on_moodle(student, student.grade)
            dbm.session.commit()

    def oralexam_revert(self, names):
        """
        Allows the user to revert the decision of marking a student as having passed the oral exam.

        Parameters:
            names (list of string): List of student names

        Returns:  Nothing
        """
        for name in names:
            student=Student.get_student_by_name(name)
            if type(student)==list:
                student=select_option_interactive(student)
            passed=Student.is_student_passed(student.name)
            if passed:
                student.grade=1
            else:
                student.grade=0
            student.oralexam_time=None
            dbm.session.commit()

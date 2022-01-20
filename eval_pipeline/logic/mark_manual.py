"""
This module provides the functionality of  manually marking submissions as passed.
This can happen if a submission passes on the reference architecture used by the students,
but not on the machine running the evaluation pipline e.g. due to different processors.
"""

import sys
import logging
import database.students as s
import database.submissions as sub
import database.runs as r
import database.database_manager as dbm
from util.select_option import select_option_interactive
from moodle.moodle_reporter import MoodleReporter
from logic.performance_evaluator import PerformanceEvaluator


class Manual:

    def __init__(self, args):
        """
        Constructor creates a MoodleReporter instance
        based on given arguments which determine the behaviour
        :param args: given commandline arguments
        """
        self.args=args

    def mark_passed_manually(self, names):
        """
        This function takes a list of student names.
        It allows the user to select a submission for each student and mark it as passed in the database.
        To record this action the flag maked_manually is set in the database for all corresponding runs of this submission.
        No performance information is set for the marked submission.

        Parameters:
            names (list of strings): List of names of students
        Returns:
            Nothing.
        """
        for name in names:
            student=s.Student.get_student_by_name(name)
            if student is None:
                print(f"No student with this name {name} found!")
                continue
            elif type(student)==list:
                student=select_option_interactive(student)
            submissions=student.submissions
            logging.debug(submissions)

            selected=None
            if len(submissions)==0:
                print(f"Student {name} has not submitted any solutions yet.")
                return
            elif len(submissions)>1:
                print("More than one submission found. Please select!")
                for index, submission in zip(range(0, len(submissions)), submissions):
                    print(f"[{index+1}]: {submission.submission_time}")

                answer_accepted=False
                answer=0
                while not answer_accepted:
                    answer=sys.stdin.readline()
                    try:
                        answer=int(answer)-1
                        if len(submissions)>answer>=0:
                            answer_accepted=True
                        else:
                            print(f"{answer+1} is not in range of"
                                  f"[{1},{len(submissions)}],"
                                  f"please select again!")
                    except ValueError:
                        print(f"{answer} is not a number,"
                              f"please select again!")
                selected=submissions[answer]


            elif len(submissions)==1:
                selected=submissions[0]
                
            for run in selected.runs:
                run.passed=True
                run.manual_overwrite_passed=True
                dbm.session.commit()

            if student.grade not in [1,2]:
                student.grade=1
                dbm.session.commit()
                reporter=MoodleReporter(self.args)
                reporter.update_grade_on_moodle(student, student.grade)
            

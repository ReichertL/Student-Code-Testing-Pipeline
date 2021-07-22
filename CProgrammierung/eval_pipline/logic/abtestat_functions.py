from datetime import  datetime
import sys

import database.database_manager as dbm
from database.students import Student
from util.select_option import select_option_interactive
from moodle.moodle_reporter import MoodleReporter


class AbtestatFunctions:

    def __init__(self, args):
        """
        Constructor creates a MoodleReporter instance
        based on given arguments which determine the behaviour
        :param args: given commandline arguments
        """
        self.args = args
        
    def abtestat_mark_as_done(self,names):

        for name in names:
            student=Student.get_student_by_name(name)
            if type(student)==list:
                student=select_option_interactive(student)  
            if not Student.is_student_passed(student.name) :
                print(f"{student.name} has not passed so far, mark abtestat as done anyways?(y/n)")
                if 'y' != sys.stdin.readline()[:1]:
                    return
                
            print(f"Please insert Mat.-Nr.!")
            answer_accepted = False
            mat_nr = 0
            while not answer_accepted:
                mat_nr = sys.stdin.readline()
                try:
                    mat_nr = int(mat_nr)
                    answer_accepted = True
                except ValueError:
                    print(f"{mat_nr} is not a number, please select again!")

            student.grade=2
            student.matrikel_nr=mat_nr
            student.abtestat_time= datetime.now()
            reporter=MoodleReporter(self.args)
            reporter.update_grade_on_moodle(student,student.grade)
            dbm.session.commit()



    def abtestat_revert(self,names):
        for name in names:
            student=Student.get_student_by_name(name)
            if type(student)==list:
                student=select_option_interactive(student)   
            passed=Student.is_student_passed(student.name)
            if passed==True:
                student.grade=1
            else:
                student.grade=0
            student.abtestat_time=None
            dbm.session.commit()

from datetime import  datetime
import sys

import alchemy.database_manager as dbm
from alchemy.students import Student
from util.select_option import select_option_interactive

class Abtestat_Functions:


    def abtestat_mark_as_done(names):

        for name in names:
            student=Student.get_student_by_name(name)
            if type(student)==list:
                student=select_option_interactive(student)  
            if not Student.is_student_passed(name) :
                print(f"{name} has not passed so far, mark abtestat as done anyways?(y/n)")
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
            dbm.session.commit()



    def abtestat_revert( names):
        for name in names:
            student=Student.get_student_by_name(name)
            if type(student)==list:
                student=select_option_interactive(student)   
            passed=Student.is_student_passed(name)
            if passed==True:
                student.grade=1
            else:
                student.grade=0
            student.abtestat_time=None
            dbm.session.commit()

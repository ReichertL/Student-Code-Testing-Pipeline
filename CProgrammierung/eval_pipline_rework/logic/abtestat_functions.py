from datetime import  datetime
import sys


class Abtestat_Functions:


    def abtestat_mark_as_done(database_manager,names):

        for name in names:
            student=database_manager.get_student_by_name(name)
            if not database_manager.is_student_passed(name) :
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
            database_manager.session.commit()



    def abtestat_revert(database_manager, names):
        for name in names:
            student=database_manager.get_student_by_name(name)
            passed=database_manager.is_student_passed(name)
            if passed==True:
                student.grade=1
            else:
                student.grade=0
            student.abtestat_time=None
            database_manager.session.commit()

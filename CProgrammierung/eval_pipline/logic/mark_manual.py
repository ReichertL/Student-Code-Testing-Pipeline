import sys
import logging

import database.students as s
import database.submissions as sub
import database.runs as r
import database.database_manager as dbm
from util.select_option import select_option_interactive

from logic.performance_evaluator import PerformanceEvaluator
 

def marke_passed_manually(names):
    for name in names:
        student = s.Student.get_student_by_name(name)
        if student is None:
            print(f"No student with this name {name} found!")
            continue
        elif type(student)==list:
           student=select_option_interactive(student)
        submissions = student.submissions
        logging.debug(submissions)
        
        selected=None
        if len(submissions)==0:
            print(f"Student {name} has not submitted any solutions yet.")
            return
        elif len(submissions) > 1:
            print("More than one submission found. Please select!")
            for index, submission in zip(range(0,len(submissions)),submissions):
                print(f"[{index + 1}]: {submission.submission_time}")

            answer_accepted = False
            answer = 0
            while not answer_accepted:
                answer = sys.stdin.readline()[0]
                try:
                    answer = int(answer) - 1
                    if len(submissions) > answer >= 0:
                        answer_accepted = True
                    else:
                        print(f"{answer + 1} is not in range of"
                                  f"[{1},{len(submissions)}],"
                                  f"please select again!")
                except ValueError:
                    print(f"{answer} is not a number,"
                              f"please select again!")                
            selected=submissions[answer]

                
        elif len(submissions)==1:
            selected=submissions[0]
        
                    
        for run in selected.runs:
            if student.grade== (0 or None): student.grade=1
            run.passed=True
            run.manual_overwrite_passed=True
            performance_evaluator = PerformanceEvaluator()
            performance_evaluator.evaluate_performance(selected,run)
            dbm.session.commit()

import sys
import logging

from database.testcases import Testcase
from database.submissions import Submission
from database.students import Student
from database.runs import Run
import database.database_manager as dbm

from logic.result_generator import ResultGenerator
from logic.test_case_executor import TestCaseExecutor
from logic.test_case_executor import sort_first_arg_and_diff
from util.colored_massages import Warn, Passed, Failed
from util.select_option import select_option_interactive
from logic.retrieve_and_compile import compile_single_submission


FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)




def execute_singel_testcase(args):

    print("Debug env to test new functionality which can be implemented, called or composed here")
    for name in args.test:
        submissions=Submission.get_last_for_name(name)
        if submissions==None:
            students=Student.get_student_by_name(name)
            student=select_option_interactive(students)
            logging.debug(student)
            submissions=Submission.get_last_for_name(student.name)

        if submissions==None:
            Warn(f"Student {name} has not submitted a solution yet or does not exist.")
            continue
        submission=submissions[0]
        testcases=Testcase.get_all()
        print(f"\nUsing Submission from the {submission.submission_time}. Please select Testcase!")
        testcase=select_option_interactive(testcases)
        print(f"\nTestcase {testcase.short_id} selected")

        result, valgrind = None,None
        executor = TestCaseExecutor(args)
        run= compile_single_submission(args,executor.configuration,submission)
        dbm.session.add(run)
        dbm.session.commit()

        if testcase.type=="BAD":
            result, valgrind = executor.check_for_error(submission,run, testcase)
        elif testcase.type=="BAD_OR_OUTPUT":
            result, valgrind = executor.check_for_error_or_output(submission,run, testcase,sort_first_arg_and_diff )
        else:
            result, valgrind =executor.check_output(submission,run,testcase,sort_first_arg_and_diff)

        ResultGenerator.print_stats_testcase_result(result, testcase, valgrind)
        logging.debug(valgrind)
        logging.debug(result)
        if valgrind is not None:
            dbm.session.delete(valgrind)
            dbm.session.commit()
        dbm.session.delete(result)
        dbm.session.commit()                
        dbm.session.delete(run)
        dbm.session.commit()



















import sys
import logging

from alchemy.testcases import Testcase
from alchemy.submissions import Submission
from alchemy.runs import Run
import alchemy.database_manager as dbm

from logic.result_generator import ResultGenerator
from logic.test_case_executor import TestCaseExecutor
from logic.test_case_executor import sort_first_arg_and_diff
from util.colored_massages import Warn, Passed, Failed


FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)




def execute_singel_testcase(args):

    print("Debug env to test new functionality which can be implemented, called or composed here")
    for name in args.test:
        submissions=Submission.get_last_for_name(name)
        if submissions==None:
            Warn(f"Student {name} has not submitted a solution yet or does not exist.")
            continue
        submission=submissions[0]
        testcases=Testcase.get_all()
        print(f"\nUsing Submission from the {submission.submission_time}. Please select Testcase!")
        for index, testcase in zip(range(0,len(testcases)),testcases):
            print(f"[{index + 1}]: {testcase.short_id}")
            answer_accepted = False
            answer = 0
        while not answer_accepted:
            
            answer = sys.stdin.readline()[0]
            try:
                answer = int(answer) - 1
                if len(testcases) > answer >= 0:
                    answer_accepted = True
                else:
                    print(f"{answer + 1} is not in range of"
                                  f"[{1},{len(testcases)}],"
                                  f"please select again!")
            except ValueError:
                print(f"{answer} is not a number,"
                              f"please select again!")

            selected=testcases[answer]
            result, valgrind = None,None
            executor = TestCaseExecutor(args)
            run= executor.compile_single_submission(submission)
            dbm.session.add(run)
            dbm.session.commit()

            if selected.type=="BAD":
                result, valgrind = executor.check_for_error(submission,run, selected)
            elif selected.type=="BAD_OR_OUTPUT":
                result, valgrind = executor.check_for_error_or_output(submission,run, selected,sort_first_arg_and_diff )
            else:
                result, valgrind =executor.check_output(submission,run,selected,sort_first_arg_and_diff)

            ResultGenerator.print_stats_testcase_result(result, selected, valgrind)

            dbm.session.delete(valgrind)
            dbm.session.commit()                
            dbm.session.delete(result)
            dbm.session.commit()                
            dbm.session.delete(run)
            dbm.session.commit()
            
                

        



















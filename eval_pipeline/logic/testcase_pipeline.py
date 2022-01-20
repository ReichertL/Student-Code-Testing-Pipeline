"""
This module manages the checking of submissions.
"""
import datetime
import os
import sys
import logging
from util.absolute_path_resolver import resolve_absolute_path
from util.colored_massages import Warn, Passed, Failed
from util.config_reader import ConfigReader
from util.result_parser import ResultParser
from util.executor_utils import unlink_safe, sort_first_arg_and_diff
from logic.executions import TestcaseExecutor
from logic.performance_evaluator import PerformanceEvaluator
from logic.result_generator import ResultGenerator
from logic.load_tests import load_tests
from logic.retrieve_and_compile import retrieve_pending_submissions, compile_single_submission
from database.testcases import Testcase
from database.submissions import Submission
from database.runs import Run
import database.database_manager as dbm
from database.students import Student
from util.select_option import select_option_interactive



FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


class TestcasePipeline:
    """
    TestcasePipeline:
    Manages the checking of submissions as well as reporting.
    Testcases are loaded here.
    """
    args={}
    configuration=""

    unshare=[]

    def __init__(self, args):
        """
        TestcasePipeline:
        Initialises TestcasePipeline. Loads testcases if required.
        Parameters:
            args :  parsed commandline arguments
        """
        raw_config_path="/resources/config_testcase_executor.config"
        config_path=resolve_absolute_path(raw_config_path)

        configuration=ConfigReader().read_file(os.path.abspath(config_path))
        self.configuration=configuration
        self.args=args
        self.executor=TestcaseExecutor(args)

        # Loads testcases if required by commandline or if no testcases exist in database
        if args.load_tests or Testcase.get_all()==[]:
            load_tests(self.configuration)

    def run(self):
        """
        Checks for all submission that are supposed to be checked, weather they compile.
        If successful, the check function is called to evaluate the submission for all testcases
        with type "GOOD", "BAD" and "BAD_OR_OUTPUT".
        If compilation was not successful, a warning is printed.
        Parameters: None
        Returns: Nothing
        """

        pending_submissions=retrieve_pending_submissions(self.args)
        if pending_submissions in [None, [], [[]]]:
            logging.info("No new submissions to check")
            return
        for submission, student in pending_submissions:
            logging.info(f'Checking Submission of {student.name} from the {submission.submission_time}')
            does_compile=compile_single_submission(self.args, self.configuration, submission)

            run=Run.insert_run(does_compile)

            if not self.args.compile:
                if run.compilation_return_code==0:
                    self.check(student, submission, run)
                    logging.info(f'Submission of '
                                    f'{student.name} submitted at '
                                    f'{submission.submission_time} did compile.')
                else:
                    logging.warning(f'Submission of '
                                    f'{student.name} submitted at '
                                    f'{submission.submission_time} did not compile.')
                    submission.is_checked=True
                    dbm.session.commit()
            else:
                logging.debug(f"Just compiled, no testcases executed")

    def check_single_testcase(self):
        """
        Executes and checks a single testcase for all the names in args.test (corresponding flag -t).
        The user can select the testcase to be run interactively.
        Does not fetch or check the whole submission. This is useful for dealing with feedback from students.
        Combined with flag -O the output of the testcase is shown.
        An additional flag -V will show Valgrind output if applicable to the selected testcase.
        No new TestcaseResult object is placed in the database by this function.

        Parameters: None
        Returns: Nothing. But prints results of executing the testcase to stdout.
        """
        logging.debug(self.args.test)
        for name in self.args.test:
            submissions=Submission.get_last_for_name(name)
            if submissions is None:
                students=Student.get_student_by_name(name)
                student=select_option_interactive(students)
                logging.debug(student)
                submissions=Submission.get_last_for_name(student.name)

            if submissions is None:
                Warn(f"Student {name} has not submitted a solution yet or does not exist.")
                continue
            submission=submissions[0]
            testcases=Testcase.get_all()
            print(f"\nUsing Submission from the {submission.submission_time}. Please select Testcase!")
            testcase=select_option_interactive(testcases)
            print(f"\nTestcase {testcase.short_id} selected")

            result, valgrind=None, None
            run=compile_single_submission(self.args, self.configuration, submission)
            dbm.session.add(run)
            dbm.session.commit()

            if testcase.type=="BAD":
                result, valgrind=self.check_for_error(submission, run, testcase)
            elif testcase.type=="BAD_OR_OUTPUT":
                result, valgrind=self.check_for_error_or_output(submission, run, testcase, sort_first_arg_and_diff)
            else:
                result, valgrind=self.check_output(submission, run, testcase, sort_first_arg_and_diff)

            ResultGenerator.print_stats_testcase_result(result, testcase, valgrind)
            if valgrind is not None:
                dbm.session.delete(valgrind)
                dbm.session.commit()
            dbm.session.delete(result)
            dbm.session.commit()
            dbm.session.delete(run)
            dbm.session.commit()

    def check(self, student, submission, run, force_performance=False):
        """
        This functions initiates the checking of the submission of this student  for all testcases
        with type "GOOD", "BAD" and "BAD_OR_OUTPUT".
        The results are committed to the database.
        Parameters:
            student (Student object):  the student which is the author of this submission.
            submission (Submission object): the submission to test
            force_performance (Boolean): tests testcases for performance too
        Returns
             True if a check was conducted, else False
        """

        if submission.is_checked:
            if self.args.rerun:
                Warn(f'You forced to re-run tests on submission by '
                     f'{student.name} submitted at {submission.submission_time}.\n'

                     f'This is submission {submission.id}'
                     f', saved at {submission.submission_path}')
            else:
                logging.info(
                    f"Not running any testcases for {student.name} because the submission from the"
                    f" {submission.submission_time} has been checked already. Use -r to rerun the submission.")
                return

        logging.info(f'running tests for '
                     f'{student.name} submitted at '
                     f'{submission.submission_time}')
        sys.stdout.flush()

        for test in Testcase.get_all_bad():
            logging.debug("Testcase BAD "+str(test.short_id))
            testcase_result, valgrind_output=self.check_for_error(submission, run, test)
            dbm.session.add(testcase_result)
            if valgrind_output is not None: dbm.session.add(valgrind_output)

        for test in Testcase.get_all_good():
            logging.debug("Testcase GOOD "+str(test.short_id))
            testcase_result, valgrind_output=self.check_output(submission, run, test, sort_first_arg_and_diff)
            dbm.session.add(testcase_result)
            if valgrind_output is not None: dbm.session.add(valgrind_output)

        # This deals with testcases that are allowed to fail gracefully,
        # but if they don't they have to return the correct value
        for test in Testcase.get_all_bad_or_output():
            logging.debug("Testcase BAD or OUTPUT "+str(test.short_id))
            testcase_result, valgrind_output=self.check_for_error_or_output(submission, run, test,
                                                                            sort_first_arg_and_diff)
            dbm.session.add(testcase_result)
            if valgrind_output is not None: dbm.session.add(valgrind_output)

        submission.is_checked=True
        dbm.session.commit()
        submission.timestamp=datetime.datetime.now()

        passed=Run.is_passed(run)
        if passed:
            run.passed=True
            if student.grade!=2:
                student.grade=1
            dbm.session.commit()
            performance_evaluator=PerformanceEvaluator()
            performance_evaluator.evaluate_performance(submission, run)
        else:
            run.passed=False
            dbm.session.commit()
        if passed and (submission.is_fast or force_performance):
            # if passed and  force_performance:
            logging.info('fast submission; running performance tests')
            for test in Testcase.get_all_performance():
                testcase_result, valgrind_output=self.check_output(submission, run, test, sort_first_arg_and_diff)
                dbm.session.add(testcase_result)
                if valgrind_output is not None: dbm.session.add(valgrind_output)

        if passed:
            Passed()
        else:
            Failed()
            if self.args.verbose:
                ResultGenerator.print_stats(run, sys.stdout)

    def check_for_error(self, submission, run, test):
        """
        Checks a submission for a "BAD" testcase.
        Here it is checked whether the submission produced the correct output for this testcase.
        No data is committed to the database here.
        Parameters:
            submission (Submission object): the submission to test
            run (Run object): Corresponding run
            test (Testcase object): testcase to execute
        Returns:
            a TestcaseResult object
            a ValgrindResult object (can be None)
        """
        testcase_result, valgrind_output=self.executor.execute_testcase(test, submission, run)
        testcase_result.error_line=''
        testcase_result.output_correct=True
        parser=ResultParser()
        parser.parse_error_file(testcase_result)
        if int(testcase_result.return_code)>0 and \
                testcase_result.error_msg_quality is not None:
            testcase_result.output_correct=True
        else:
            testcase_result.output_correct=False
        logging.debug(
            f"FAIL  Testcase, check for error: output correct {testcase_result.output_correct}, "
            f"return_code {testcase_result.return_code} {(int(testcase_result.return_code))},"
            f" error_msg_quality {testcase_result.error_msg_quality}")
        unlink_safe("test.stderr")
        unlink_safe("test.stdout")
        return testcase_result, valgrind_output

    def check_output(self, submission, run, test, comparator):
        """
        Checks a submission for a "GOOD" testcase.
        Here it is checked whether the submission produced the correct output for this testcase.
        No data is committed to the database here.
        Parameters:
            submission (Submission object): the submission to test
            run (Run object): Corresponding run
            test (Testcase object): testcase to execute
            comparator (Function pointer): A function that should be used to determine if the output is correct.
        Returns:
            a TestcaseResult object
            a ValgrindResult object (can be None)
        """
        testcase_result, valgrind_output=self.executor.execute_testcase(test, submission, run)
        testcase_result.output_correct=comparator('test.stdout', os.path.join(test.path+'.stdout'))
        unlink_safe("test.stderr")
        unlink_safe("test.stdout")
        return testcase_result, valgrind_output

    def check_for_error_or_output(self, submission, run, test, comparator):
        """
        Checks a submission for a "BAD_OR_OUTPUT" testcase.
        Here it is checked whether the submission produced the correct output for this testcase.
        No data is committed to the database here.
        Parameters:
            submission (Submission object): the submission to test
            run (Run object): Corresponding run
            test (Testcase object): testcase to execute
            comparator (Function pointer): A function that should be used to determine if the output is correct.
        Returns:
            a TestcaseResult object
            a ValgrindResult object (can be None)
        """
        testcase_result, valgrind_output=self.executor.execute_testcase(test, submission, run)
        testcase_result.output_correct=comparator('test.stdout', os.path.join(test.path+'.stdout'))
        if testcase_result.output_correct is False:
            testcase_result.error_line=''
            testcase_result.output_correct=True
            parser=ResultParser()
            parser.parse_error_file(testcase_result)
            if testcase_result.return_code>0 and \
                    testcase_result.error_msg_quality>0:
                testcase_result.output_correct=True
            else:
                testcase_result.output_correct=False
        unlink_safe("test.stderr")
        unlink_safe("test.stdout")
        return testcase_result, valgrind_output

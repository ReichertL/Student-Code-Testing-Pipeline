"""
This module manages all test case execution and evaluation
"""
import time
import datetime
import os
import resource
import subprocess
import sys
import logging
FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)

from util.absolute_path_resolver import resolve_absolute_path
from util.colored_massages import Warn, Passed, Failed
from util.config_reader import ConfigReader
from util.named_pipe_open import NamedPipeOpen
from util.result_parser import ResultParser
from util.executor_utils import unlink_safe,unlink_as_cpr,getmtime,sort_first_arg_and_diff,sudokill

from logic.performance_evaluator import PerformanceEvaluator
from logic.result_generator import ResultGenerator
from logic.load_tests import load_tests
from logic.retrieve_and_compile import retrieve_pending_submissions, compile_single_submission


from database.testcases import Testcase
from database.submissions import Submission
from database.runs import Run
from database.testcase_results import Testcase_Result
import database.database_manager as dbm
#from database.students import Student
from database.valgrind_outputs import Valgrind_Output




global limits


class TestCaseExecutor:
    """
    TestCaseExecutor:
    manages test case execution and compilation as well as reporting
    :parameter
        args :  parsed commandline arguments
    """
    args = {}
    configuration = ""
    sudo_user = ''
    sudo = []
    unshare = []

    def __init__(self, args):

        raw_config_path = "/resources/config_test_case_executor.config"
        config_path = resolve_absolute_path(raw_config_path)

        configuration = ConfigReader().read_file(os.path.abspath(config_path))
        self.configuration = configuration
        self.args = args
        sudo_path = configuration["SUDO_PATH"]
        sudo_user = configuration["SUDO_USER"]
        self.sudo = [sudo_path, '-u', sudo_user]

        unshare_path = configuration["UNSHARE_PATH"]
        self.unshare = [unshare_path, '-r', '-n']
        if args.load_tests:
            load_tests(self.configuration) 

    def run(self):
        """
            runs specified test cases
        """
        
        pending_submissions = retrieve_pending_submissions(self.args)
        if pending_submissions in [None,[], [[]]]:
            logging.info("No new submissions to check")
            return
        for submission, student in pending_submissions:
            logging.info(f'Checking Submission of {student.name} from the {submission.submission_time}')
            does_compile = compile_single_submission(self.args,self.configuration,submission)

            run=Run.insert_run(does_compile)
          
 
            if (not len(self.args.compile) > 0):
                if run.compilation_return_code==0:
                    testcase_results = self.check( student,submission,run)
                else:
                    logging.warn(f'Submission of '
                        f'{student.name} submitted at '
                        f'{submission.submission_time} did not compile.')
                    submission.is_checked = True
                    dbm.session.commit()
            else: 
                logging.debug(f"Just compiled, no testcases executed")


            


    def check(self,  student,submission, run, force_performance=False):
        """
        checks the submission of a student
        :param student: the student which is the author of this submission
        :param submission: the submission to test
        :param force_performance: tests test_cases for performance too
        :return: true if a check was conducted, else false
        """

        source = submission.submission_path
        if submission.is_checked:
            if self.args.rerun:
                Warn(f'You forced to re-run tests on submission by '
                     f'{student.name} submitted at {submission.submission_time}.\n'

                     f'This is submission {submission.id}'
                     f', saved at {submission.submission_path}')
            else:
                logging.info(f"Not running any testcases for {student.name} because the submission from the {submission.submission_time} has been checked already. Use -r to rerun the submission.")
                return
            
        logging.info(f'running tests for '
              f'{student.name} submitted at '
              f'{submission.submission_time}')
        sys.stdout.flush()

        if True: 
        #if compiled.compilation_return_code== 0:
            for test in Testcase.get_all_bad():
                logging.debug("Testcase BAD "+str(test.short_id))
                testcase_result, valgrind_output = self.check_for_error(submission,run, test)
                dbm.session.add(testcase_result)
                if not valgrind_output == None: dbm.session.add(valgrind_output)
                
            for test in Testcase.get_all_good():
                 logging.debug("Testcase GOOD "+str(test.short_id))

                 testcase_result, valgrind_output =self.check_output(submission,run,test,sort_first_arg_and_diff)
                 dbm.session.add(testcase_result)
                 if not valgrind_output == None: dbm.session.add(valgrind_output)
                
            #This deals with testcases that are allowed to fail gracefully, but if they don't they have to return the correct value
            for test in Testcase.get_all_bad_or_output():
                logging.debug("Testcase BAD or OUTPUT "+str(test.short_id))
                testcase_result, valgrind_output = self.check_for_error_or_output(submission,run, test, sort_first_arg_and_diff )
                dbm.session.add(testcase_result)
                #logging.debug("FAIL  Testcase, check for error: output correct {testcase_result.output_correct}, return_code {testcase_result.return_code} {(int(testcase_result.return_code))}, error_msg_quality {testcase_result.error_msg_quality}"

                if not valgrind_output == None: dbm.session.add(valgrind_output)
                           
            dbm.session.commit()
        else:
            Warn(f'Something went wrong! '
                     f'Submission by {student.name} submitted at {submission.submission_time}'
                     f' did not compile but compiled earlier.\n'
                     f'This is submission {submission.id}'
                     f', saved at {submission.submission_path}')
        
        submission.is_checked = True
        dbm.session.commit()
        submission.timestamp = datetime.datetime.now()

        passed = Run.is_passed(run)
        if passed:
            run.passed=True
            if student.grade !=2:
                student.grade=1
            dbm.session.commit()
            performance_evaluator = PerformanceEvaluator()
            performance_evaluator.evaluate_performance(submission,run)
        else: 
            run.passed=False
            dbm.session.commit()
        if passed and (submission.is_fast or force_performance):
        #if passed and  force_performance:
            logging.info('fast submission; running performance tests')                
            for test in Testcase.get_all_performance():  
                testcase_result, valgrind_output =self.check_output(submission,run,test,sort_first_arg_and_diff)
                dbm.session.add(testcase_result)
                if not valgrind_output == None: dbm.session.add(valgrind_output)

        if passed and submission.is_fast:
            #performance_evaluator \     #TODO Wozu ist das hier??
             #   .average_euclidean_cpu_time_competition(submission)
            Passed()
        elif passed:
            Passed()
        else:
            Failed()
            if self.args.verbose:
                ResultGenerator.print_stats(run,sys.stdout)        


    def check_for_error(self, submission, run, test):
        """
        checks a submission for a bad input test case
        :param submission: the submission to test
        :param test: test case to execute
        :param verbose: enables verbose output
        :return: returns the result of the testcase
        """
        testcase_result, valgrind_output = self.execute_testcase(test, submission,run)
        testcase_result.error_line = ''
        testcase_result.output_correct = True
        parser = ResultParser()
        parser.parse_error_file(testcase_result)
        if int(testcase_result.return_code) > 0 and \
               testcase_result.error_msg_quality != None:
            testcase_result.output_correct = True
        else:
            testcase_result.output_correct = False
        logging.debug(f"FAIL  Testcase, check for error: output correct {testcase_result.output_correct}, return_code {testcase_result.return_code} {(int(testcase_result.return_code))}, error_msg_quality {testcase_result.error_msg_quality}")
        unlink_safe("test.stderr")
        unlink_safe("test.stdout")
        return testcase_result,valgrind_output
    
    
    def check_output(self, submission, run, test, comparator ):
        """
        Checks a testcase that should be successful
        :param test: test case to execute
        :param submission: submission to test
        :param verbose: enables verbose input
        :param comparator: compares to results
        :return: a TestCaseResult object encapsulating the results
        """
        testcase_result, valgrind_output = self.execute_testcase(test, submission,run )
        testcase_result.output_correct = comparator('test.stdout', os.path.join(test.path + '.stdout'))
        unlink_safe("test.stderr")
        unlink_safe("test.stdout")
        return testcase_result, valgrind_output
    
    
    def check_for_error_or_output(self, submission, run, test,comparator):
        """
        checks a submission for a bad input test case
        :param submission: the submission to test
        :param test: test case to execute
        :param verbose: enables verbose output
        :return: returns the result of the testcase
        """
        testcase_result, valgrind_output = self.execute_testcase(test, submission,run)
        testcase_result.output_correct = comparator('test.stdout', os.path.join(test.path + '.stdout'))
        if testcase_result.output_correct==False:
            testcase_result.error_line = ''
            testcase_result.output_correct = True
            parser = ResultParser()
            parser.parse_error_file(testcase_result)
            if testcase_result.return_code > 0 and \
                    testcase_result.error_msg_quality > 0:
                testcase_result.output_correct = True
            else:
                testcase_result.output_correct = False
        unlink_safe("test.stderr")
        unlink_safe("test.stdout")
        return testcase_result,valgrind_output


    def execute_testcase(self, testcase, submission,run):
        """
        tests a submission with a testcaseabtestat
        :param submission: the submission to test
        :param test_case: the test_case object encapsulating
        paths and expected results
        :param verbose: enables verbose output
        :return: returns a test_case_result object
        """
 
        parser = ResultParser()
        result = Testcase_Result.create_or_update(run.id,testcase.id)
        if self.args.verbose:
            logging.info(f'--- executing '
                  f'{"".join(submission.submission_path.split("/")[-2:])} '
                  f'< {testcase.short_id} ---')
        tic = time.time()
        

        
        with NamedPipeOpen(f"{testcase.path}.stdin") as fin, \
                open('test.stdout', 'bw') as fout, \
                open('test.stderr', 'bw') as ferr:
            out,err=fout,ferr
            if self.args.output==True:
                out=sys.stdout
                err=sys.stderr
                logging.info("\nExecutable output:\n")
            args = ['./loesung']
            global limits
            limits=self.get_limits(testcase)
            #logging.debug(f"limits {limits}")
            p = subprocess.Popen(
                self.sudo
                + self.unshare
                + [self.configuration["TIME_PATH"],
                   "-f", '%S %U %M %x %e', '-o',
                   self.configuration["TIME_OUT_PATH"]]
                + args,
                stdin=fin,
                stdout=out,
                stderr=err,
                preexec_fn=self.set_limits,
                cwd='/tmp')
            try:
                p.wait(150)
            except subprocess.TimeoutExpired:
                sudokill(p)
            duration = time.time() - tic
            result.return_code = p.returncode
            if p.returncode in (-9, -15, None):
                result.timeout=True
                if result.return_code is None:
                    result.return_code = -15
                duration = -1
            else:
                #sets timeout, segfault, signal,mrss, cpu_time
                with open(self.configuration["TIME_OUT_PATH"]) as file:
                    parser.parse_time_file(result, file)
            if self.args.verbose and result.timeout:
                logging.info('-> TIMEOUT')
            result.tictoc = duration  
            result.rlimit_data=limits[0]
            result.rlimit_stack=limits[1]
            result.rlimit_cpu=limits[2]
            result.num_executions=1
            fin.close()

            if self.args.verbose:
                logging.info(f'--- finished '
                      f'{"".join(submission.submission_path.split("/")[-2:])} '
                      f'< {testcase.short_id} ---')

        valgrind_output=None
        if testcase.valgrind_needed and (not result.timeout) and (not result.segfault):
            out, err=subprocess.DEVNULL,subprocess.DEVNULL
            if self.args.verbose:
                logging.info(f'--- executing valgrind '
                      f'{"".join(submission.submission_path.split("/")[-2:])} '
                      f'< {testcase.short_id} ---')
            with NamedPipeOpen(f"{testcase.path}.stdin") as fin:
                p = subprocess.Popen(self.sudo
                                     + self.unshare
                                     + [self.configuration["VALGRIND_PATH"],
                                        '--log-file='
                                        #+ "/tmp/valgrind"
                                        #+testcase.short_id]
                                        #+ args,
                                     + self.configuration["VALGRIND_OUT_PATH"]]
                                     + args,
                                     stdin=fin,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL,
                                     #preexec_fn=self.set_limits,
                                     cwd='/tmp')
                try:
                    p.wait(300)
                except subprocess.TimeoutExpired:
                    sudokill(p)
            if p.returncode not in (-9, -15, None):
                try:
                    with open(self.configuration["VALGRIND_OUT_PATH"], 'br') as f:
                        valgrind_output=Valgrind_Output.create_or_get(result.id)
                        valgrind_output= parser.parse_valgrind_file(valgrind_output,f)
                    if self.args.valgrind==True:
                        with open(self.configuration["VALGRIND_OUT_PATH"], 'br') as f:
                            logging.info("\nValgrind output:\n")
                            for line in f.readlines():
                                logging.info(line)
                            #logging.info("\n")
                except FileNotFoundError:
                    logging.error("Valgrind output file was not found.")
                    pass
            if self.args.verbose:
                logging.info(f'--- finished valgrind '
                      f'{"".join(submission.submission_path.split("/")[-2:])} < '
                      f'{testcase.short_id} ---')
            unlink_as_cpr(self.configuration["VALGRIND_OUT_PATH"], self.sudo)

        return result, valgrind_output
    
    def get_limits(self,testcase):
        if not self.args.final and testcase.rlimit==None:
            return [self.configuration["RLIMIT_DATA"],self.configuration["RLIMIT_STACK"],self.configuration["RLIMIT_CPU"]]
        elif not self.args.final:
            data_limit=max(testcase.rlimit,10000000)
            return [data_limit,self.configuration["RLIMIT_STACK"],self.configuration["RLIMIT_CPU"]]
        else: 
            data_limit=max(testcase.rlimit,10000000)
            return [data_limit*self.configuration["RLIMIT_DATA_CARELESS_FACTOR"],self.configuration["RLIMIT_STACK_CARELESS"],self.configuration["RLIMIT_CPU_CARELESS"]]  
            

    
    def set_limits(self):
        """
        Sets runtime ressources depending on the possible
        final flag
        nothing
        """
        global limits
        resource.setrlimit(resource.RLIMIT_DATA,2 * (limits[0],))
        resource.setrlimit(resource.RLIMIT_STACK,2 * (limits[1],))
        resource.setrlimit(resource.RLIMIT_CPU,2 * (limits[2],))


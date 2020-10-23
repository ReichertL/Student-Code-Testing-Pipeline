"""
This module manages all test case execution and evaluation
"""
import datetime
import json
import os
import resource
import subprocess
import sys
import tempfile
import time
import logging

from logic.performance_evaluator import PerformanceEvaluator
from models.compilation import Compilation
from models.test_case import TestCase
from models.test_case_result import TestCaseResult
from util.absolute_path_resolver import resolve_absolute_path
from util.colored_massages import Warn, Passed, Failed
from util.config_reader import ConfigReader
from util.gcc import hybrid_gcc, native_gcc
from util.named_pipe_open import NamedPipeOpen
from util.result_parser import ResultParser


from alchemy.testcases import Testcase
from alchemy.submissions import Submission
from alchemy.runs import Run
from alchemy.testcase_results import Testcase_Result
from alchemy.database_manager import DatabaseManager


FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)



def unlink_safe(path):
    """
    Removes a file
    :param path: file to remove
    """
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def unlink_as_cpr(path, sudo):
    """
    Removes a file as sudo
    :param path: the file to remove
    :param sudo: call params as sudo
    """
    if os.path.exists(path):
        subprocess.call(sudo + ['rm', path])


def getmtime(path):
    """
    returns the mtime for a file
    :param path: the configuration to the file
    :return: the mtime
    """
    return int(os.path.getmtime(path))


def sort_first_arg_and_diff(f1, f2):
    """
    Sorts and compares two files
    :param f1: file 1
    :param f2: file 2
    :return: whether the content is equal or not
    """
    f1_sorted = tempfile.mktemp()
    f2_sorted = tempfile.mktemp()
    subprocess.run(['sort', f1, '-o', f1_sorted])
    subprocess.run(['sort', f2, '-o', f2_sorted])
    res = (subprocess.run(['diff', '-q', f1_sorted, f2_sorted],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0)
    unlink_safe(f1_sorted)
    unlink_safe(f2_sorted)
    return res


def sudokill(process):
    """
    Calls kill on a process as sudo
    :param process: the process to kill
    """
    subprocess.call(['sudo', 'kill', str(process.pid)],
                    stderr=subprocess.DEVNULL)


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

    def run(self, database_manager):
        """
            runs specified test cases
        """
        self.load_tests(database_manager)  #TODO: Mit flag versehen, so dass testcases nur eingelesen werden wenn es manuell gefordert wird

        pending_submissions = self.retrieve_pending_submissions(database_manager)
        for submission in pending_submissions:
            student=database_manager.get_student_by_submission(submission)
            run = self.compile_single_submission(submission)
            database_manager.session.add(run)
            database_manager.session.commit()    
                
            if (not len(self.args.compile) > 0):
                if run.compilation_return_code==0:
                    testcase_results = self.check(database_manager, student,submission,run)
                else:
                    print(f'Submission of '
                        f'{student.name} submitted at '
                        f'{submission.submission_time} did not compile.')
            
    def retrieve_pending_submissions(self, database_manager):
        """Extracts submissions that should be evaluated
        based on the commandline arguments
        :return: list of submissions
        """
        submissions = []

        if self.args.check:
            for name in self.args.check:
                submissions_student=database_manager.get_submissions_not_checked_for_name(name)
                submissions.extend(submissions_student)
                    
                

        if self.args.all:
            submissions=database_manager.get_submissions_not_checked()
                        

        if self.args.unpassed:
            students = database_manager.get_students_not_passed()
            logging.debug(students)
            for student in students:
                submissions_students=database_manager.get_all_submissions_for_name(student.name)
                submissions.extend(submissions_students)
        logging.debug(submissions)
        return submissions


    def compile_single_submission(self, submission, strict=True):
        path=submission.submission_path
        """Tries to compile a c file at configuration
        @:param configuration string describing
        the configuration of the configuration c file
        @:param strict
                boolean describing whether
                -Werror' should be used as gcc flag
        @:return Compilation object
                (gcc_return_code, commandline call , gcc_stderr)
        """

        gcc_args = [self.configuration["GCC_PATH"]] + \
                   self.configuration["CFLAGS"]

        if self.args.final:
            gcc_args = [self.configuration["GCC_PATH"]] + \
                       self.configuration["CFLAGS_CARELESS"]

        if not strict:
            gcc_args.remove('-Werror')
        submission_executable_path = '/tmp/loesung'
        commandline, return_code, gcc_stderr = hybrid_gcc(  
            gcc_args,
            path,
            submission_executable_path,
            self.configuration['DOCKER_IMAGE_GCC'],
            self.configuration['DOCKER_CONTAINER_GCC'],
            self.configuration['DOCKER_SHARED_DIRECTORY'])
        return Run(submission.id,commandline, return_code, gcc_stderr)

    def load_tests(self, database_manager):
        """
        Loads the in the config file specified testcases for good bad and extra
        :return: dictionary of list test_case
        test_case_type -> [test_cases]
        """
        test_cases = {}
        extensions = {"BAD": self.configuration["TESTS_BAD_EXTENSION"],
                      "GOOD": self.configuration["TESTS_GOOD_EXTENSION"],
                      "EXTRA": self.configuration["TESTS_EXTRA_EXTENSION"]}
        test_case_id = 0
        json_descriptions = {}

        for key in extensions:

            test_case_input = []
            path_prefix = os.path.join(resolve_absolute_path(self.configuration["TESTS_BASE_DIR"]),
                                       extensions[key])
            for root, _, files in os.walk(
                    path_prefix
                    ,
                    topdown=False):
                for name in files:

                    if name.endswith(".stdin"):
                        short_id = name.replace(".stdin", "")
                        path=os.path.join(root, name).replace(".stdin", "")
                        #logging.debug(short_id)

                        json_file=(root+"/"+name).replace(".stdin", ".json")
                        if(os.path.exists(json_file)):
                            with open(json_file) \
                                    as description_file:
                                json_rep=json.load(description_file)
                                description = json_rep["short_desc"]
                                hint = json_rep["hint"]
                                #logging.debug(root)
                                type=json_rep["type"]
                                testcase = Testcase(path, short_id, description, hint, type)
                                database_manager.testcase_create_or_update(testcase)
                                #logging.debug(testcase)
                        else: 
                            description= short_id
                            hint = f"bei {short_id}"
                            type="UNSPEZIFIED"
                            if extensions["GOOD"] in root: type="GOOD"
                            elif extensions["BAD"] in root: type="BAD"
                            elif extensions["EXTRA"] in root: type="EXTRA" #TODO:support for other types here?
                            #logging.debug(root)
                            testcase = Testcase(path, short_id, description, hint, type)
                            database_manager.testcase_create_or_update(testcase)

    def check(self, database_manager, student,submission, run, force_performance=False):
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
                return
        print(f'running tests for '
              f'{student.name} submitted at '
              f'{submission.submission_time}')
        sys.stdout.flush()
        compiled= self.compile_single_submission(submission)



        if compiled.compilation_return_code== 0:
            for test in database_manager.get_testcases_bad():
                logging.debug("Testcase "+str(test.short_id))
                testcase_result, valgrind_output = self.check_for_error(submission,run, test)
                database_manager.session.add(testcase_result)
                if not valgrind_output == None: database_manager.session.add(valgrind_output)
                
            for test in database_manager.get_testcases_good():
                logging.debug("Testcase "+str(test.short_id))

                testcase_result, valgrind_output =self.check_output(submission,run,test,sort_first_arg_and_diff)
                database_manager.session.add(testcase_result)
                if not valgrind_output == None: database_manager.session.add(valgrind_output)
                
            #This deals with testcases that are allowed to fail gracefully, but if they don't they have to return the correct value
            for test in database_manager.get_testcases_bad_or_output():
                logging.debug("Testcase "+str(test.short_id))
                testcase_result, valgrind_output = self.check_for_error_or_output(submission,run, test, sort_first_arg_and_diff )
                database_manager.session.add(testcase_result)
                if not valgrind_output == None: database_manager.session.add(valgrind_output)
                            
            database_manager.session.commit()
        else:
            Warn(f'Something went wrong! '
                     f'Submission by {student.name} submitted at {submission.submission_time}'
                     f' did not compile but compiled earlier.\n'
                     f'This is submission {submission.id}'
                     f', saved at {submission.submission_path}')
        
        submission.is_checked = True
        database_manager.session.commit()
        submission.timestamp = datetime.datetime.now()

        passed = database_manager.run_is_passed(run)
        if passed:
            student.grade=1
            database_manager.session.commit()
            performance_evaluator = PerformanceEvaluator()
            performance_evaluator.evaluate_performance(submission,run,database_manager)
        #if passed and (submission.is_fast or force_performance):
        if passed and  force_performance:
            print('fast submission; running performance tests')                
            for test in database_manager.get_testcases_performace():  
                testcase_result, valgrind_output =self.check_output(submission,run,test,sort_first_arg_and_diff)
                database_manager.session.add(testcase_result)
                if not valgrind_output == None: database_manager.session.add(valgrind_output)

        if run.passed and submission.is_fast:
            #performance_evaluator \     #TODO Wozu ist das hier??
             #   .average_euclidean_cpu_time_competition(submission)
            Passed()

        else:
            Failed()
            if self.args.verbose:
                run.print_stats()        

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
        if testcase_result.return_code > 0 and \
                testcase_result.error_msg_quality > 0:
            testcase_result.output_correct = True
        else:
            testcase_result.output_correct = False
        unlink_safe("test.stderr")
        unlink_safe("test.stdout")
        return testcase_result,valgrind_output

    def check_output(self, submission, run, test, comparator):
        """
        Checks a testcase that should be successful
        :param test: test case to execute
        :param submission: submission to test
        :param verbose: enables verbose input
        :param comparator: compares to results
        :return: a TestCaseResult object encapsulating the results
        """
        testcase_result, valgrind_output = self.execute_testcase(test, submission,run)
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
        limits=self.get_limits_time()
        parser = ResultParser()
        result = Testcase_Result(run.id,testcase.id)
        if self.args.verbose:
            print(f'--- executing '
                  f'{"".join(submission.submission_path.split("/")[-2:])} '
                  f'< {testcase.short_id} ---')
        tic = time.time()
        with NamedPipeOpen(f"{testcase.path}.stdin") as fin, \
                open('test.stdout', 'bw') as fout, \
                open('test.stderr', 'bw') as ferr:
            args = ['./loesung']
            p = subprocess.Popen(
                self.sudo
                + self.unshare
                + [self.configuration["TIME_PATH"],
                   "-f", '%S %U %M %x %e', '-o',
                   self.configuration["TIME_OUT_PATH"]]
                + args,
                stdin=fin,
                stdout=fout,
                stderr=ferr,
                preexec_fn=self.set_limits_time(limits),
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
                print('-> TIMEOUT')
            result.tictoc = duration            
            result.rlimit_data=limits[0]
            result.rlimit_stack=limits[1]
            result.rlimit_cpu=limits[2]
            fin.close()

            if self.args.verbose:
                print(f'--- finished '
                      f'{"".join(submission.submission_path.split("/")[-2:])} '
                      f'< {testcase.short_id} ---')

        valgrind_output=None
        if testcase.valgrind_needed and (not result.timeout) and (not result.segfault):
            if self.args.verbose:
                print(f'--- executing valgrind '
                      f'{"".join(submission.submission_path.split("/")[-2:])} '
                      f'< {testcase.short_id} ---')
            with NamedPipeOpen(f"{testcase.submission_path}.stdin") as fin:
                p = subprocess.Popen(self.sudo
                                     + self.unshare
                                     + [self.configuration["VALGRIND_PATH"],
                                        '--log-file='
                                        + self
                                     .configuration["VALGRIND_OUT_PATH"]]
                                     + args,
                                     stdin=fin,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL,
                                     preexec_fn=self.set_limits_valgrind(limits),
                                     cwd='/tmp')
                try:
                    p.wait(300)
                except subprocess.TimeoutExpired:
                    sudokill(p)
            if p.returncode not in (-9, -15, None):
                try:
                    with open(self.configuration["VALGRIND_OUT_PATH"], 'br') as f:
                        valgrind_output= parser.parse_valgrind_file(testcase.id,f)
                except FileNotFoundError:
                    pass
            if self.args.verbose:
                print(f'--- finished valgrind '
                      f'{"".join(submission.submission_path.split("/")[-2:])} < '
                      f'{testcase.short_id} ---')
            unlink_as_cpr(self.configuration["VALGRIND_OUT_PATH"], self.sudo)
        return result, valgrind_output

    def get_limits_time(self):
        if not self.args.final:
            return [self.configuration["RLIMIT_DATA"],self.configuration["RLIMIT_STACK"],self.configuration["RLIMIT_CPU"]]
        else: 
            return [self.configuration["RLIMIT_DATA_CARELESS"],self.configuration["RLIMIT_STACK_CARELESS"],self.configuration["RLIMIT_CPU_CARELESS"]]  
    
    def set_limits_time(self, limits):
        """
        Sets runtime ressources depending on the possible
        final flag
        nothing
        """
        resource.setrlimit(resource.RLIMIT_DATA,2 * (limits[0],))
        resource.setrlimit(resource.RLIMIT_STACK,2 * (limits[1],))
        resource.setrlimit(resource.RLIMIT_CPU,2 * (limits[2],))



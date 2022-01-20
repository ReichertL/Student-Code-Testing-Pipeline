"""
Here the functionality for spawning child processes for executing testcases. 
"""
import glob
import os
import resource
import shutil
import subprocess
from subprocess import DEVNULL, PIPE
import sys
import logging
#from datetime import time
import  time
from pwd import getpwnam
from database.testcases import Testcase
from database.submissions import Submission
from database.students import Student
from database.runs import Run
import database.database_manager as dbm
from database.testcase_results import TestcaseResult
from database.valgrind_outputs import ValgrindOutput
from logic.result_generator import ResultGenerator
from logic.retrieve_and_compile import compile_single_submission
from util.colored_massages import Warn, Passed, Failed
from util.select_option import select_option_interactive
from util.result_parser import ResultParser
from util.executor_utils import unlink_safe, unlink_as_cpr, getmtime, sort_first_arg_and_diff, sudokill
from util.named_pipe_open import NamedPipeOpen
from util.absolute_path_resolver import resolve_absolute_path
from util.config_reader import ConfigReader

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

OWN_PW=getpwnam(os.environ['USER'])
OWN_UID_GID=f'{OWN_PW.pw_uid:d}.{OWN_PW.pw_gid:d}'
SUDO_DOCKER=['sudo', 'docker']


class TestcaseExecutor:
    args={}
    configuration=""
    sudo_user=''
    sudo=[]
    unshare=[]
    limits=None

    def __init__(self, args):
        """
         TestcaseExecutor:
         Initialises TestcaseExecutor. Reads config file to load other information.
         Parameters:
             args :  parsed commandline arguments
         """
        raw_config_path="/resources/config_testcase_executor.config"
        config_path=resolve_absolute_path(raw_config_path)

        configuration=ConfigReader().read_file(os.path.abspath(config_path))
        self.configuration=configuration
        self.args=args
        sudo_path=configuration["SUDO_PATH"]
        sudo_user=configuration["SUDO_USER"]
        self.sudo=[sudo_path, '-u', sudo_user]

        unshare_path=configuration["UNSHARE_PATH"]
        self.unshare=[unshare_path, '-r', '-n']
        self.docker_container=self.configuration["DOCKER_CONTAINER_GCC"]
        self.docker_image=self.configuration["DOCKER_IMAGE_GCC"]
        self.shared_dir=self.configuration["DOCKER_SHARED_DIRECTORY"]
        
        self.make_home_private()

    def make_home_private(self):
        """
        This function aims minimizing the gain of an manicious user uploading code which reads the file system and sends it across the internet. 
        The aim is that the malicious student should not be able to learn the submissions of other students or other private data. 
        This can be done using unshare, but that is not possible inside a docker container for other security reasons. 
        Therefor we assume that the server running this code is only used for running this pipeline. 
        We make the home directory of the default user only readable to its owner and execute submissions with the "cpr" user. This user therefore has no access to any data related to the default user. 
        """
        name= "CHMOD_HOME_QUERY"
        try:
            is_set=os.environ[name]
        except:
            is_set=None
        if is_set!="1":
            env_user=os.environ['USER']
            path=f"/home/{env_user}"
            logging.warning("For ALL files of user {env_user} Permissions will be changed to only be readable,writeable and executable by the owner (700).")
            res=select_option_interactive(['Yes','NO (This option has security risks)'])
            if res=='Yes':
                os.system(f' sudo sh -c "chmod -R o-rwx {path}/*"')
            logging.debug(f'export {name}="1"')
            with open(os.path.expanduser("~/.bashrc"), "a") as outfile:
                outfile.write(f'export {name}="1"')
                        
   



    def execute_testcase(self, testcase, submission, run):
        """
        Runs a submission with a testcase by creating subprocess.
        For the subprocess data, stack  and CPU limits are set.
        The process is killed if it takes longer than 150 seconds for execution.
        Results are stored in a TestcaseResult object, but not committed to the database.

        If no timeout occurred and it is required, the submission is also checked with Valgrind.
        Here the subprocess has a timeout of 300 seconds.
        No limits are set for the subprocess which checks using Valgrind.
        Results are stored in a ValgrindOutput object, but not committed to the database.

        Parameters:
            testcase (Testcase object): testcase to be checked
            submission (Submission object): Submission handed in by student
            run (Run object): Run corresponding to the submission.

        Returns:
            TestcaseResult object
            ValgrindOutput object (can be None)
        """

        parser=ResultParser()
        result=TestcaseResult.create_or_get(run.id, testcase.id)
        if self.args.verbose:
            logging.info(f'--- executing '
                         f'{"".join(submission.submission_path.split("/")[-2:])} '
                         f'< {testcase.short_id} ---')
        tic=time.time()

        with NamedPipeOpen(f"{testcase.path}.stdin") as fin, \
                open('test.stdout', 'bw') as fout, \
                open('test.stderr', 'bw') as ferr:
            out, err=fout, ferr
            if self.args.output:
                out=sys.stdout
                err=sys.stderr
                logging.info("\nExecutable output:\n")
            c_args=['./loesung']
            self.limits=self.get_limits(testcase)

            # equivalent to:
            # cd /tmp && cat ~/eval_pipeline/resources/testcases/good/example_sheet.stdin  |  sudo unshare -r -n /usr/bin/htime  -f  %S %U %M %x %e -o /tmp/test-time.out ./loesung 2> test.stderr 1> test.stdout
            command=self.sudo\
                +[self.configuration["TIME_PATH"],\
                "-f", '%S %U %M %x %e', '-o',\
                self.configuration["TIME_OUT_PATH"]]\
                +c_args
            p=subprocess.Popen(
                command,
                stdin=fin,
                stdout=out,
                stderr=err,
                preexec_fn=self.set_limits,
                cwd='/tmp')
            try:
                p.wait(150)
            except subprocess.TimeoutExpired:
                sudokill(p)
            duration=time.time()-tic
            result.return_code=p.returncode
            if p.returncode in (-9, -15, None):
                result.timeout=True
                if result.return_code is None:
                    result.return_code=-15
                duration=-1
            else:
                # sets timeout, segfault, signal,mrss in Bytes, cpu_time in seconds
                with open(self.configuration["TIME_OUT_PATH"]) as file:
                    parser.parse_time_file(result, file)
            if self.args.verbose and result.timeout:
                logging.info('-> TIMEOUT')
            result.tictoc=duration
            result.rlimit_data=self.limits[0]
            result.rlimit_stack=self.limits[1]
            result.rlimit_cpu=self.limits[2]
            result.num_executions=1
            fin.close()

            if self.args.verbose:
                logging.info(f'--- finished '
                             f'{"".join(submission.submission_path.split("/")[-2:])} '
                             f'< {testcase.short_id} ---')

        valgrind_output=None
        if testcase.valgrind_needed and (not result.timeout) and (not result.segfault):
            valgrind_output=self.execute_valgrind(submission, testcase, result, c_args)

        return result, valgrind_output
    
    def execute_testcase_docker(self, testcase, submission, run):
        """
        #TODO : THIS FUNCTION IS UNFINISHED. DO NOT USE
        Runs a submission with a testcase by creating subprocess.
        For the subprocess data, stack  and CPU limits are set.
        The process is killed if it takes longer than 150 seconds for execution.
        Results are stored in a TestcaseResult object, but not committed to the database.

        If no timeout occurred and it is required, the submission is also checked with Valgrind.
        Here the subprocess has a timeout of 300 seconds.
        No limits are set for the subprocess which checks using Valgrind.
        Results are stored in a ValgrindOutput object, but not committed to the database.

        Parameters:
            testcase (Testcase object): testcase to be checked
            submission (Submission object): Submission handed in by student
            run (Run object): Run corresponding to the submission.

        Returns:
            TestcaseResult object
            ValgrindOutput object (can be None)
        """

        parser=ResultParser()
        result=TestcaseResult.create_or_get(run.id, testcase.id)
        if self.args.verbose:
            logging.info(f'--- executing '
                         f'{"".join(submission.submission_path.split("/")[-2:])} '
                         f'< {testcase.short_id} ---')
        tic=time.time()

        if len(os.listdir(self.shared_dir))!=0:
            logging.info(f"clearing {self.shared_dir}")
            files=glob.glob(f'{self.shared_dir}/*')
            for f in files:
                os.remove(f)


        # create docker container, if it does not exist already
        run(SUDO_DOCKER+['create',
                         '--name', self.configuration["DOCKER_CONTAINER_GCC"],
                         '-v', f'{self.shared_dir}:/host',
                         self.configuration["DOCKER_IMAGE_GCC"]],
            stdout=DEVNULL,
            stderr=DEVNULL)

        # start docker container if required
        cp=run(SUDO_DOCKER+['start', self.docker_container], stdout=DEVNULL, stderr=sys.stderr)
        if cp.returncode!=0:
            logging.info(cp)
            raise DockerError(
                f'Unable to start docker container {self.docker_container} based on docker image {self.docker_image}.')

        # copy c file
        tmp_c_basename=os.path.basename(dest)+'.c'
        tmp_c_path=os.path.join(self.shared_dir, tmp_c_basename)
        shutil.copy(src, tmp_c_path)



        # execute gcc in docker container
        all_args=gcc_args+['-o', os.path.basename(dest),
                           os.path.basename(dest)+'.c']
        commandline=' '.join(all_args)

        command_full=SUDO_DOCKER+['exec',
                                  '-w', '/host',
                                  self.docker_container,
                                  'bash', '-c',
                                  f'{commandline} 2> gcc.stderr ; '
                                  'echo $? > gcc.return ;'
                                  f'chown {OWN_UID_GID} gcc.stderr gcc.return {os.path.basename(dest)}']
        cp=run(command_full,
               stdout=DEVNULL,
               stderr=DEVNULL)
        with open(os.path.join(self.shared_dir, 'gcc.stderr')) as f:
            gcc_stderr=f.read()
        os.unlink(os.path.join(self.shared_dir, 'gcc.stderr'))
        with open(os.path.join(self.shared_dir, 'gcc.return')) as f:
            gcc_returncode=int(next(f))
        os.unlink(os.path.join(self.shared_dir, 'gcc.return'))

        with NamedPipeOpen(f"{testcase.path}.stdin") as fin, \
                open('test.stdout', 'bw') as fout, \
                open('test.stderr', 'bw') as ferr:
            out, err=fout, ferr
            if self.args.output:
                out=sys.stdout
                err=sys.stderr
                logging.info("\nExecutable output:\n")
            c_args=['./loesung']
            self.limits=self.get_limits(testcase)

            # equivalent to:
            # cd /tmp && cat ~/eval_pipeline/resources/testcases/good/example_sheet.stdin  |  sudo unshare -r -n /usr/bin/htime  -f  %S %U %M %x %e -o /tmp/test-time.out ./loesung 2> test.stderr 1> test.stdout
            p=subprocess.Popen(
                self.sudo
                +self.unshare
                +[self.configuration["TIME_PATH"],
                  "-f", '%S %U %M %x %e', '-o',
                  self.configuration["TIME_OUT_PATH"]]
                +c_args,
                stdin=fin,
                stdout=out,
                stderr=err,
                preexec_fn=self.set_limits,
                cwd='/tmp')
            try:
                p.wait(150)
            except subprocess.TimeoutExpired:
                sudokill(p)
            duration=time.time()-tic
            result.return_code=p.returncode
            if p.returncode in (-9, -15, None):
                result.timeout=True
                if result.return_code is None:
                    result.return_code=-15
                duration=-1
            else:
                # sets timeout, segfault, signal,mrss in Bytes, cpu_time in seconds
                with open(self.configuration["TIME_OUT_PATH"]) as file:
                    parser.parse_time_file(result, file)
            if self.args.verbose and result.timeout:
                logging.info('-> TIMEOUT')
            result.tictoc=duration
            result.rlimit_data=self.limits[0]
            result.rlimit_stack=self.limits[1]
            result.rlimit_cpu=self.limits[2]
            result.num_executions=1
            fin.close()

            if self.args.verbose:
                logging.info(f'--- finished '
                             f'{"".join(submission.submission_path.split("/")[-2:])} '
                             f'< {testcase.short_id} ---')

        valgrind_output=None
        if testcase.valgrind_needed and (not result.timeout) and (not result.segfault):
            valgrind_output=self.execute_valgrind(submission, testcase, result, c_args)

        return result, valgrind_output

    def execute_testcase_unshare(self, testcase, submission, run):
        """
        Runs a submission with a testcase by creating subprocess.
        For the subprocess data, stack  and CPU limits are set.
        The process is killed if it takes longer than 150 seconds for execution.
        Results are stored in a TestcaseResult object, but not committed to the database.

        If no timeout occurred and it is required, the submission is also checked with Valgrind.
        Here the subprocess has a timeout of 300 seconds.
        No limits are set for the subprocess which checks using Valgrind.
        Results are stored in a ValgrindOutput object, but not committed to the database.
        
        Uses unshare to ensure an malicious student can not  read out home directory. This function can therefore not be used in an docker environment.

        Parameters:
            testcase (Testcase object): testcase to be checked
            submission (Submission object): Submission handed in by student
            run (Run object): Run corresponding to the submission.

        Returns:
            TestcaseResult object
            ValgrindOutput object (can be None)
        """

        parser=ResultParser()
        result=TestcaseResult.create_or_get(run.id, testcase.id)
        if self.args.verbose:
            logging.info(f'--- executing '
                         f'{"".join(submission.submission_path.split("/")[-2:])} '
                         f'< {testcase.short_id} ---')
        tic=time.time()

        with NamedPipeOpen(f"{testcase.path}.stdin") as fin, \
                open('test.stdout', 'bw') as fout, \
                open('test.stderr', 'bw') as ferr:
            out, err=fout, ferr
            if self.args.output:
                out=sys.stdout
                err=sys.stderr
                logging.info("\nExecutable output:\n")
            c_args=['./loesung']
            self.limits=self.get_limits(testcase)

            # equivalent to:
            # cd /tmp && cat ~/eval_pipeline/resources/testcases/good/example_sheet.stdin  |  sudo unshare -r -n /usr/bin/htime  -f  %S %U %M %x %e -o /tmp/test-time.out ./loesung 2> test.stderr 1> test.stdout
            p=subprocess.Popen(
                self.sudo
                +self.unshare
                +[self.configuration["TIME_PATH"],
                  "-f", '%S %U %M %x %e', '-o',
                  self.configuration["TIME_OUT_PATH"]]
                +c_args,
                stdin=fin,
                stdout=out,
                stderr=err,
                preexec_fn=self.set_limits,
                cwd='/tmp')
            try:
                p.wait(150)
            except subprocess.TimeoutExpired:
                sudokill(p)
            duration=time.time()-tic
            result.return_code=p.returncode
            if p.returncode in (-9, -15, None):
                result.timeout=True
                if result.return_code is None:
                    result.return_code=-15
                duration=-1
            else:
                # sets timeout, segfault, signal,mrss in Bytes, cpu_time in seconds
                with open(self.configuration["TIME_OUT_PATH"]) as file:
                    parser.parse_time_file(result, file)
            if self.args.verbose and result.timeout:
                logging.info('-> TIMEOUT')
            result.tictoc=duration
            result.rlimit_data=self.limits[0]
            result.rlimit_stack=self.limits[1]
            result.rlimit_cpu=self.limits[2]
            result.num_executions=1
            fin.close()

            if self.args.verbose:
                logging.info(f'--- finished '
                             f'{"".join(submission.submission_path.split("/")[-2:])} '
                             f'< {testcase.short_id} ---')

        valgrind_output=None
        if testcase.valgrind_needed and (not result.timeout) and (not result.segfault):
            valgrind_output=self.execute_valgrind(submission, testcase, result, c_args)

        return result, valgrind_output

    def execute_valgrind(self, submission, testcase, result, c_args):
        """

        This function checks with valgrind if a submission is sound.
        Here subprocess has a timeout of 300 seconds.
        No limits are set for the subprocess which checks using Valgrind.
        Results are stored in a ValgrindOutput object, but not committed to the database.

        Parameters:
            testcase (Testcase object): testcase to be checked
            submission (Submission object): Submission handed in by student
            result (TestcaseResult object): The results from the corresponding "normal" testcase execution.
            c_args: list of arguments used for calling the executable. Usually that's ["./loesung"]

        Returns:
            ValgrindOutput object (can be None)
        """

        parser=ResultParser()
        out, err=subprocess.DEVNULL, subprocess.DEVNULL
        if self.args.verbose:
            logging.info(f'--- executing valgrind '
                         f'{"".join(submission.submission_path.split("/")[-2:])} '
                         f'< {testcase.short_id} ---')
        
        out=subprocess.DEVNULL
        err=subprocess.DEVNULL
        
        if self.args.valgrind:
            out=sys.stdout
            err=sys.stderr
            
        with NamedPipeOpen(f"{testcase.path}.stdin") as fin:
            # corresponds to:
            # sudo -u cpr /usr/bin/valgrind --log-file=/tmp/test.valgrind.out ./loesung
            command=self.sudo\
                +[self.configuration["VALGRIND_PATH"]]\
                +[f'--log-file={self.configuration["VALGRIND_OUT_PATH"]}']\
                +c_args
                               
            p=subprocess.Popen(command,
                               stdin=fin,
                               stdout=out,
                               stderr=err,
                               # preexec_fn=self.set_limits,
                               cwd='/tmp')
            try:
                p.wait(300)
            except subprocess.TimeoutExpired:
                sudokill(p)
        valgrind_output=None
        if p.returncode not in (-9, -15, None):
            try:
                with open(self.configuration["VALGRIND_OUT_PATH"], 'br') as f:
                    valgrind_output=ValgrindOutput.create_or_get(result.id)
                    valgrind_output=parser.parse_valgrind_file(valgrind_output, f)
                if self.args.valgrind:
                    with open(self.configuration["VALGRIND_OUT_PATH"], 'br') as f:
                        logging.info("\nValgrind output:\n")
                        for line in f.readlines():
                            logging.info(line)
                        # logging.info("\n")
            except FileNotFoundError:
                logging.error("Valgrind output file was not found.")
                pass
        if self.args.verbose:
            logging.info(f'--- finished valgrind '
                         f'{"".join(submission.submission_path.split("/")[-2:])} < '
                         f'{testcase.short_id} ---')
        unlink_as_cpr(self.configuration["VALGRIND_OUT_PATH"], self.sudo)
        return valgrind_output
    
    def execute_valgrind_unshare(self, submission, testcase, result, c_args):
        """
        This function checks with valgrind if a submission is sound.
        Here subprocess has a timeout of 300 seconds.
        No limits are set for the subprocess which checks using Valgrind.
        Results are stored in a ValgrindOutput object, but not committed to the database.

        Uses unshare to ensure an malicious student can not  read out home directory. This function can therefore not be used in an docker environment.


        Parameters:
            testcase (Testcase object): testcase to be checked
            submission (Submission object): Submission handed in by student
            result (TestcaseResult object): The results from the corresponding "normal" testcase execution.
            c_args: list of arguments used for calling the executable. Usually that's ["./loesung"]

        Returns:
            ValgrindOutput object (can be None)

        """
        parser=ResultParser()
        out, err=subprocess.DEVNULL, subprocess.DEVNULL
        if self.args.verbose:
            logging.info(f'--- executing valgrind '
                         f'{"".join(submission.submission_path.split("/")[-2:])} '
                         f'< {testcase.short_id} ---')
        with NamedPipeOpen(f"{testcase.path}.stdin") as fin:
            p=subprocess.Popen(self.sudo
                               +self.unshare
                               +[self.configuration["VALGRIND_PATH"]
                                 +'--log-file='
                                 +self.configuration["VALGRIND_OUT_PATH"]]
                               +c_args,
                               stdin=fin,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,
                               # preexec_fn=self.set_limits,
                               cwd='/tmp')
            try:
                p.wait(300)
            except subprocess.TimeoutExpired:
                sudokill(p)
        if p.returncode not in (-9, -15, None):
            try:
                with open(self.configuration["VALGRIND_OUT_PATH"], 'br') as f:
                    valgrind_output=ValgrindOutput.create_or_get(result.id)
                    valgrind_output=parser.parse_valgrind_file(valgrind_output, f)
                if self.args.valgrind:
                    with open(self.configuration["VALGRIND_OUT_PATH"], 'br') as f:
                        logging.info("\nValgrind output:\n")
                        for line in f.readlines():
                            logging.info(line)
                        # logging.info("\n")
            except FileNotFoundError:
                logging.error("Valgrind output file was not found.")
                pass
        if self.args.verbose:
            logging.info(f'--- finished valgrind '
                         f'{"".join(submission.submission_path.split("/")[-2:])} < '
                         f'{testcase.short_id} ---')
        unlink_as_cpr(self.configuration["VALGRIND_OUT_PATH"], self.sudo)
        return valgrind_output


    def get_limits(self, testcase):
        """
        Returns resource limits based on command line flags and the testcase.
        Testcases can have their individual resource limits which can be set in the .json file
        which corresponds to the testcase.



        Parameters:
            testcase (Testcase object): Testcase for which the

        Returns:
            List of Integers, representing limits for the data segment of the process, the stack size
            and the available CPU resources

        """
        if not self.args.final and testcase.rlimit is None:
            return [self.configuration["RLIMIT_DATA"], self.configuration["RLIMIT_STACK"],
                    self.configuration["RLIMIT_CPU"]]
        elif not self.args.final:
            data_limit=max(testcase.rlimit, 10000000)
            return [data_limit, self.configuration["RLIMIT_STACK"], self.configuration["RLIMIT_CPU"]]
        else:
            data_limit=max(testcase.rlimit, 10000000)
            return [data_limit*self.configuration["RLIMIT_DATA_CARELESS_FACTOR"],
                    self.configuration["RLIMIT_STACK_CARELESS"], self.configuration["RLIMIT_CPU_CARELESS"]]

    def set_limits(self):
        """
        Sets runtime resources for a process using the class variable limits.
        Run for the subprocess before a testcase is executed for a submission.
        Parameters: None
        Returns: Nothing
        """
        # global limits
        resource.setrlimit(resource.RLIMIT_DATA, 2*(self.limits[0],))
        resource.setrlimit(resource.RLIMIT_STACK, 2*(self.limits[1],))
        resource.setrlimit(resource.RLIMIT_CPU, 2*(self.limits[2],))


class DockerError(RuntimeError):
    pass

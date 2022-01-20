"""
This module manages finding submissions to be checked and compiling submissions
"""
import logging
from util.select_option import select_option_interactive
from util.gcc import hybrid_gcc, native_gcc
from database.submissions import Submission
from database.runs import Run
from database.students import Student

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


def retrieve_pending_submissions(args):
    """
        Using the commandline arguments, this functions selects the submissions which will be evaluated.
        Parameters:
            args (ArgumentParser object): commandline arguments
        Returns:
            List of Submission objects
        """
    submissions=[]

    if args.check and args.rerun:
        for name in args.check:
            submissions_student=Submission.get_last_for_name(name)
            if submissions_student is not None:
                submissions.append(submissions_student)
            else:
                students=Student.get_student_by_name(name)
                student=select_option_interactive(students)
                logging.debug(student)
                submissions_student=Submission.get_last_for_name(student.name)
                if submissions_student is not None:
                    submissions.append(submissions_student)

    elif args.check:
        for name in args.check:
            submissions_student=Submission.get_not_checked_for_name(name)
            submissions.append(submissions_student)

    if args.all:
        submissions=Submission.get_not_checked()

    if args.unpassed:
        students=Student.get_students_not_passed()
        logging.debug(students)
        for student in students:
            submissions_students=Submission.get_all_for_name(student.name)
            submissions.extend(submissions_students)
    return submissions


def compile_single_submission(args, configuration, submission, strict=True):
    """
    Tries to compile a c file with a given configuration

    Parameters:
        args (ArgumentParser object): Commandline arguments
        configuration (dict): Describes the configuration of the configuration c file
        strict (boolean): Describes whether '-Werror' should be used as gcc flag

    Returns:
         Run object
    """
    path=submission.submission_path
    careless_flag=False
    gcc_args=[configuration["GCC_PATH"]]+ \
             configuration["CFLAGS"]

    if args.final:
        gcc_args=[configuration["GCC_PATH"]]+ \
                 configuration["CFLAGS_CARELESS"]
        careless_flag=True

    if not strict:
        gcc_args.remove('-Werror')
    submission_executable_path='/tmp/loesung'
    commandline, return_code, gcc_stderr=hybrid_gcc(
        gcc_args,
        path,
        submission_executable_path,
        configuration['DOCKER_IMAGE_GCC'],
        configuration['DOCKER_CONTAINER_GCC'],
        configuration['DOCKER_SHARED_DIRECTORY'])
    return Run(submission.id, commandline, careless_flag, return_code, gcc_stderr)

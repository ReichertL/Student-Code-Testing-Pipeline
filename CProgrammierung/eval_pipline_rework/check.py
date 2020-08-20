#!/usr/bin/env python3

"""
driver program, that encapsulates business logic and controls based on
commandline arguments the behavior of the evaluation of student
submissionsParameter: none, reads commandline arguments to determine behavior
"""
import os
from signal import SIGABRT, SIGTERM, SIGSEGV, SIGILL, signal, SIGINT

from logic.database_integrator import DatabaseIntegrator
from logic.moodle_reporter import MoodleReporter
from logic.moodle_submission_fetcher import MoodleSubmissionFetcher
from logic.result_generator import ResultGenerator
from logic.test_case_executor import TestCaseExecutor
from persistence.database_manager import SQLiteDatabaseManager
from util.argument_extractor import ArgumentExtractor
from util.lockfile import LockFile
from util.playground import Playground

LOCK_FILE_PATH = '/run/lock/check.lock'

def run():
    """
    Reading commandline arguments,
    due to readability extracted to separate module and invokes
    in args specified functionality
    """
    try:
        argument_extractor = ArgumentExtractor()
        args = argument_extractor.get_arguments()
        database_manager = SQLiteDatabaseManager()
        database_manager.create()
        if args.fetch or args.fetch_only:
            # Execute Submission Fetching if needed determined by the provided args
            fetcher = MoodleSubmissionFetcher(args)
            fetcher.run(database_manager)
            database_integrator = DatabaseIntegrator()
            database_integrator.integrate_submission_dir(database_manager)

        studentlog = database_manager.get_all_students()
        for student in studentlog:
            student.get_all_submissions(database_manager)

        if not args.fetch_only:
            # Execute test cases if needed determined by the provided args
            executor = TestCaseExecutor(args)
            executor.run(database_manager=database_manager)

        # Send Moodle feedback to students if needed determined by args
        if args.mail_to_all or len(args.mailto) > 0 or args.debug:
            reporter = MoodleReporter(args)
            reporter.run(database_manager=database_manager)

        result_generator = ResultGenerator()
        if len(args.abtestat) > 0:
            students = [database_manager.get_student_by_name(student_name) for student_name in args.abtestat]
            for student in students:
                database_manager.mark_as_done(student)
        if len(args.revert) > 0:
            students = [database_manager.get_student_by_name(student_name) for student_name in args.revert]
            for student in students:
                database_manager.revert_abtestat(student)

        if args.generate:
            result_generator.generate_csv_dump(database_manager)

        if args.stats:
            result_generator.print_short_stats(database_manager)

        if len(args.details) > 0:
            result_generator.print_details(database_manager, args.details)

        if args.playground:
            playground = Playground()
            playground.run()
    finally:
        try:
            database_manager.close()
        except:
            pass


if __name__ == "__main__":
    with LockFile(LOCK_FILE_PATH):
        run()

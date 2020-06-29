#!/usr/bin/env python3

"""
driver program, that encapsulates business logic and controls based on
commandline arguments the behavior of the evaluation of student
submissionsParameter: none, reads commandline arguments to determine behavior
"""

from logic.database_integrator import DatabaseIntegrator
from logic.moodle_reporter import MoodleReporter
from logic.moodle_submission_fetcher import MoodleSubmissionFetcher
from logic.test_case_executor import TestCaseExecutor

from persistence.database_manager import SQLiteDatabaseManager
from util.argument_extractor import ArgumentExtractor
from util.playground import Playground


def run():
    """
    Reading commandline arguments,
    due to readability extracted to separate module and invokes
    in args specified functionality
    """

    argument_extractor = ArgumentExtractor()
    args = argument_extractor.get_arguments()
    verbosity = args.verbose
    persistence_manager = SQLiteDatabaseManager()
    persistence_manager.create()
    if args.fetch or args.fetch_only:
        # Execute Submission Fetching if needed determined by the provided args
        fetcher = MoodleSubmissionFetcher(args)
        fetcher.run(persistence_manager)
        database_integrator = DatabaseIntegrator()
        database_integrator.integrate_submission_dir(persistence_manager)

    studentlog = persistence_manager.get_all_students()
    for student in studentlog:
        student.get_all_submissions(persistence_manager)

    if not args.fetch_only:
        # Execute test cases if needed determined by the provided args
        executor = TestCaseExecutor(args)
        executor.run(database_manager=persistence_manager, verbosity=verbosity)

    # Send Moodle feedback to students if needed determined by args
    if args.mail_to_all or len(args.mailto) > 0 or args.debug:
        reporter = MoodleReporter(args)
        reporter.run(database_manager=persistence_manager)

    if args.playground:
        playground = Playground()
        playground.run()

    persistence_manager.close()

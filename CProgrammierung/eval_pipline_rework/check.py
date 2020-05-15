#!/usr/bin/env python3

"""
driver program, that encapsulates business logic and controls based on
commandline arguments the behavior of the evaluation of student
submissionsParameter: none, reads commandline arguments to determine behavior
"""

from logic.moodle_reporter import MoodleReporter
from logic.moodle_submission_fetcher import MoodleSubmissionFetcher
from logic.test_case_executor import TestCaseExecutor
from models.student import Student
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
    persistence_manager.insert_student(Student("hallo", "15255", "1266"))
    persistence_manager.insert_student(Student("hallo", "15255", "1263"))

    # Execute Submission Fetching if needed determined by the provided args
    fetcher = MoodleSubmissionFetcher(args)

    # Execute test cases if needed determined by the provided args
    executor = TestCaseExecutor(args)
    executor.run()

    # Send Moodle feedback to students if needed determined by args
    reporter = MoodleReporter(args)

    if args.playground:
        playground = Playground()
        playground.run()

    persistence_manager.close()

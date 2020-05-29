#!/usr/bin/env python3

"""
driver program, that encapsulates business logic and controls based on
commandline arguments the behavior of the evaluation of student
submissionsParameter: none, reads commandline arguments to determine behavior
"""

from logic.moodle_reporter import MoodleReporter
from logic.moodle_submission_fetcher import MoodleSubmissionFetcher
from logic.test_case_executor import TestCaseExecutor
from models.compilation import Compilation
from models.student import Student
from models.submission import Submission

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
    new_student = Student("Mark Spitzner", "MoodelID", persistence_manager)
    if len(persistence_manager.get_submissions_for_student(new_student)) == 0:
        persistence_manager.insert_submission(new_student, Submission(compilation=Compilation(0, "test", "test")))
    students = persistence_manager.get_all_students()
    submissions = persistence_manager.get_submissions_for_student(new_student)
    for submission in submissions:
        print(submission)



    # Execute Submission Fetching if needed determined by the provided args
    fetcher = MoodleSubmissionFetcher(args)

    # Execute test cases if needed determined by the provided args
    executor = TestCaseExecutor(args)
    executor.run(database_manager=persistence_manager)
    tests = executor.test_cases

    # Send Moodle feedback to students if needed determined by args
    reporter = MoodleReporter(args)

    if args.playground:
        playground = Playground()
        playground.run()

    persistence_manager.close()

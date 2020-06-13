#!/usr/bin/env python3

"""
driver program, that encapsulates business logic and controls based on
commandline arguments the behavior of the evaluation of student
submissionsParameter: none, reads commandline arguments to determine behavior
"""

from logic.database_integrator import DatabaseIntegrator
from logic.test_case_executor import TestCaseExecutor
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
    if args.fetch or args.fetch_only:
        test = False
        # Execute Submission Fetching if needed determined by the provided args
        # fetcher = MoodleSubmissionFetcher(args)
        if not test:
            database_integrator = DatabaseIntegrator()
            database_integrator.integrate_submission_dir(persistence_manager)

        if persistence_manager.is_empty() and test:
            test_sub = Submission()
            test_sub.path = \
                "/home/mark/Uni/SHK2020/ds/CProgrammierung/musterloesung/" \
                "Musterloesung_Mark/loesung.c"
            new_student_one = \
                Student("Mark Spitzner", "MoodelID", persistence_manager)
            persistence_manager.insert_submission(new_student_one, test_sub)
            test_sub = Submission()
            test_sub.path = \
                "/home/mark/projects/eval_pipline_rework/resources/test.c"
            persistence_manager.insert_submission(new_student_one, test_sub)

    studentlog = persistence_manager.get_all_students()
    for student in studentlog:
        student.get_all_submissions(persistence_manager)

    if not args.fetch_only:
        # Execute test cases if needed determined by the provided args
        executor = TestCaseExecutor(args)
        executor.run(database_manager=persistence_manager, verbosity=verbosity)

    # Send Moodle feedback to students if needed determined by args
    # reporter = MoodleReporter(args)

    if args.playground:
        playground = Playground()
        playground.run()

    persistence_manager.close()

#!/usr/bin/env python3

"""
driver program, that encapsulates business logic and controls based on
commandline arguments the behavior of the evaluation of student
submissionsParameter: none, reads commandline arguments to determine behavior
"""
import os
import traceback
import logging
from signal import SIGABRT, SIGTERM, SIGSEGV, SIGILL, signal, SIGINT

from moodel.database_integrator import DatabaseIntegrator
from moodel.moodle_reporter import MoodleReporter
from moodel.moodle_submission_fetcher import MoodleSubmissionFetcher
from logic.performance_evaluator import PerformanceEvaluator
from logic.result_generator import ResultGenerator
from logic.test_case_executor import TestCaseExecutor
from logic.abtestat_functions import Abtestat_Functions
from util.argument_extractor import ArgumentExtractor
from util.lockfile import LockFile
from util.playground import Playground
from database.database_manager import DatabaseManager 
from logic.mark_manual import marke_passed_manually
from logic.execute_single import execute_singel_testcase

LOCK_FILE_PATH = '/run/lock/check.lock'
FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)




def run():
    """
    Reading commandline arguments,
    due to readability extracted to separate module and invokes
    in args specified functionality
    """
    try:

                
        argument_extractor = ArgumentExtractor()
        args = argument_extractor.get_arguments()
        database_manager=DatabaseManager()        
        ##database_manager = SQLiteDatabaseManager()
        ##database_manager.create()
        if args.fetch or args.fetch_only:
            # Execute Submission Fetching if needed determined by the provided args
            fetcher = MoodleSubmissionFetcher(args)
            fetcher.run()
            database_integrator = DatabaseIntegrator()
            database_integrator.integrate_submission_dir()

        if not args.fetch_only:
            # Execute test cases if needed determined by the provided args
            executor = TestCaseExecutor(args)
            executor.run()
        # Send Moodle feedback to students if needed determined by args
        if args.mail_to_all or len(args.mailto) > 0 or args.debug:
            reporter = MoodleReporter(args)
            reporter.run()

        # marks students as abtestat done or reverts this operation
        if len(args.abtestat) > 0:
           Abtestat_Functions.abtestat_mark_as_done(args.abtestat)
            
        if len(args.revert) > 0:
            Abtestat_Functions.abtestat_revert( args.revert)

        if len(args.mark_manual) > 0:
            marke_passed_manually(args.mark_manual)

        result_generator = ResultGenerator()
        # generates a csv dump for moodle grading
        if args.generate:
            result_generator.generate_csv_dump()
        # prints short statistics for all submissions
        if args.stats:
            result_generator.print_summary_stats_small()

        # prints detailed information about a specific student submission
        if len(args.details) > 0:
            result_generator.print_details(args.details)

        # evaluates and shows performance statistics for all students which have passed
        if args.show_performance:
            performance_evaluator = PerformanceEvaluator()
            performance_evaluator.evaluate()
            
        if len(args.test)>0:
            execute_singel_testcase(args)            

        # optional playground to try new implemented features
        if args.playground:
            playground=Playground()
            playground.run()

    finally:
        try:
            cleanup()
            database_manager.close()
        except:
            pass


if __name__ == "__main__":
    with LockFile(LOCK_FILE_PATH):
        run()
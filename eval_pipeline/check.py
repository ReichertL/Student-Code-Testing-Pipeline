#!/usr/bin/env python3

"""
This is a driver program, that encapsulates business logic and controls based on
commandline arguments the behavior of the evaluation of student
submissions.

Parameters: 
    none, reads commandline arguments to determine behavior
"""
import os
import traceback
import logging
from signal import SIGABRT, SIGTERM, SIGSEGV, SIGILL, signal, SIGINT
from datetime import datetime

from moodle.database_integrator import DatabaseIntegrator
from moodle.moodle_reporter import MoodleReporter
from moodle.moodle_submission_fetcher import MoodleSubmissionFetcher
from database.database_manager import DatabaseManager
from logic.performance_evaluator import PerformanceEvaluator
from logic.result_generator import ResultGenerator
from logic.testcase_pipeline import TestcasePipeline
from logic.oralexam_functions import OralExamFunctions
from logic.mark_manual import Manual
from util.argument_extractor import ArgumentExtractor
from util.lockfile import LockFile
from util.playground import Playground

LOCK_FILE_PATH='/run/lock/check.lock'
FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

args=None


def run():
    """
    Reading commandline arguments.
    Uses separate module and  the passed commandline arguments to run the specified functionality.
    """
    now=datetime.now()
    dt_string=now.strftime("%d/%m/%Y %H:%M:%S")

    logging.info(
        f"\n-----------------------------------------------------------\nEval Pipline  (Current Time: {dt_string})")

    try:
        # extracting commandline arguments
        argument_extractor=ArgumentExtractor()
        global args
        args=argument_extractor.get_arguments()
        database_manager=DatabaseManager()

        # If -f or --fetch-only: Fetch new submission from moodle.
        # If not fetch only also executes and evaluates them
        if args.fetch or args.fetch_only:
            fetcher=MoodleSubmissionFetcher(args)
            fetcher.run()
            database_integrator=DatabaseIntegrator()
            database_integrator.integrate_submission_dir()
            if args.fetch_only:
                exit(0)

        if args.check or args.all or args.unpassed:
            pipeline=TestcasePipeline(args)
            pipeline.run()

        # Send Moodle feedback to students. Requires flag -m or flag -M  and a student name. 
        if args.mail_to_all or len(args.mailto)>0:
            reporter=MoodleReporter(args)
            reporter.run()

        # Marks oral exam  as done for a specific student. Requires flag -A and student name
        if len(args.oralexam)>0:
            oralexam_func=OralExamFunctions(args)
            oralexam_func.oralexam_mark_as_done(args.oralexam)

        # Mark oral exam as NOT completed for a specific student. Requires flag -R and student name
        if len(args.revert)>0:
            oralexam_func=OralExamFunctions(args)
            oralexam_func.oralexam_revert(args.revert)

        # Manually mark a submission of a student as passed. Requires flag -D and student name
        if len(args.mark_manual)>0:
            man=Manual(args)
            man.mark_passed_manually(args.mark_manual)

        # Generates a csv dump for moodle grading
        result_generator=ResultGenerator()
        # If flag -g, generate csv dump
        if args.generate:
            result_generator.generate_csv_dump()
        # If flag -s, prints short statistics for all submissions
        if args.stats:
            result_generator.print_summary_stats_small(args)

        # If flag -d , prints detailed information about a specific student submission
        if len(args.details)>0:
            result_generator.print_details(args.details)

        # Evaluates and shows performance statistics for all students which have passed
        if args.show_performance:
            performance_evaluator=PerformanceEvaluator()
            performance_evaluator.evaluate()

        # Allows the execution of a single testcase for a student. Requires flag -t and a students name.
        # Helpful here are flags -o to show the output of the test and -v for valgrind output.
        if len(args.test)>0:
            pipeline=TestcasePipeline(args)
            pipeline.check_single_testcase()

            # Optional playground to try new implemented features
        if args.playground:
            playground=Playground()
            playground.run()

    finally:
        try:
            cleanup()
            database_manager.close()
        except:
            pass


if __name__=="__main__":
    with LockFile(LOCK_FILE_PATH):
        run()

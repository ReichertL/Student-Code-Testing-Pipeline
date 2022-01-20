"""
 Contains only ArgumentExtractor which encapsulates
 reading arguments from the command line
 """

import argparse


class ArgumentExtractor:
    """
    Encapsulates reading arguments from the command line
    implements.
    Usage:
        init_parser(self)
        get_arguments(self)
    """

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.init_parser()

    def init_parser(self):
        """
        Implements the initialization of an argument parser
        if you need to read additional commandline arguments,
        please add them here!

        """
        self \
            .parser \
            .add_argument('-f', '--fetch',
                          dest='fetch',
                          action='store_true',
                          help='Fetch new submissions')
        self \
            .parser \
            .add_argument('--fetch-only',
                          dest='fetch_only',
                          action='store_true',
                          help='Fetch new submissions and exits afterwards.')
        self \
            .parser \
            .add_argument('--load_tests',
                          dest='load_tests',
                          action='store_true',
                          help='Load all testcases from resources/testcases.')
        self \
            .parser \
            .add_argument('-c', '--check',
                          dest='check',
                          type=str,
                          default=[],
                          action="append",
                          help='Run tests for the submissions'
                               ' of the given student'
                               ' Usage: check -c "Firstname Lastname"' )
        self \
            .parser \
            .add_argument('-a', '--all',
                          action='store_true',
                          help='Run tests for all submissions')
        self \
            .parser \
            .add_argument('-t', '--test',
                          dest='test',
                          nargs='*',
                          type=str,
                          default=[],
                          help='Allows user to provide a student name'
                              ' and select a test to be run for their last submission.'
                              ' Usage: check -t "Firstname Lastname"')
        self \
            .parser \
            .add_argument('-O', '--output',
                          dest="output",
                          action='store_true',
                          help='Prints output from executed sumbission' 
                               ' Usage for exaple:  check -Ot "Firstname Lastname" OR  check -fav')
        self \
            .parser \
            .add_argument('-V', '--valgrind',
                          dest="valgrind",
                          action='store_true',
                          help='Prints valgrind output from executed sumbissions.'
                            'Usage for exaple: check -Vt "Firstname Lastname" or check -favV')
        self \
            .parser \
            .add_argument('-C', '--compile',
                          dest='compile',
                          type=str,
                          default='',
                          help='Just compile this configuration')
        self \
            .parser \
            .add_argument('-e', '--extra',
                          nargs='*',
                          dest='extra_sources',
                          type=str,
                          default=[],
                          help='Run extra tests for each submission'
                               'that has not been tested so far')
        self \
            .parser \
            .add_argument('-s', '--stats',
                          dest='stats',
                          action='store_true',
                          help='Print stats for all students. '
                               'Do test new configuration files. Usage: check -s')
        self \
            .parser \
            .add_argument('-v', '--verbose',
                          dest='verbose',
                          action='store_true',
                          help='Print detailed test results'
                               ' for each test executed')
        self \
            .parser \
            .add_argument('-d', '--details',
                          nargs='*',
                          dest='details',
                          type=str,
                          default=[],
                          help='Print details for single student. Usage: check -d "Firstnam Lastname"')


        self \
            .parser \
            .add_argument('-M', '--mail',
                          nargs='*',
                          dest='mailto',
                          type=str,
                          default=[],
                          help='Send Mail to single or a list of students. Usage check -M "Firstname Lastname"')
        self \
            .parser.add_argument('-U',
                                 dest='mail_manual',
                                 action='store_true',
                                 help='Send mail reports to everyone '
                                      'who has not received a report'
                                      ' for the current version yet. Requires manual verification.')


        self \
            .parser.add_argument('-m', '--mailtoall',
                                 dest='mail_to_all',
                                 action='store_true',
                                 help='Send mail reports to everyone '
                                      'who has not received a report'
                                      ' for the current version yet')


        self \
            .parser. \
            add_argument('-b', '--best',
                         action='store_true',
                         help='Combined with -d:'
                              ' shows best submission'
                              ' instead of latest')
        self \
            .parser \
            .add_argument('-p', '--performance',
                          dest='show_performance',
                          action='store_true')

        self \
            .parser \
            .add_argument('-H', '--html',
                          dest='html_performance_output',
                          action='store_true')
        self \
            .parser \
            .add_argument('-F', '--final',
                          action='store_true')
        self \
            .parser \
            .add_argument('-r', '--rerun',
                          action='store_true',
                          help='Rerun submissions that have already been checked.'
                               ' Usage: check -rc "Firstname Lastname"'
                          )
        self \
            .parser \
            .add_argument('-P', '--playground',
                          dest='playground',
                          action='store_true',
                          help='Playground')
        self \
            .parser \
            .add_argument('--sim',
                          action='store_true',
                          help='Perform all-to-all similarity check')
        self \
            .parser \
            .add_argument('--exit-status',
                          action='store_true',
                          help='If used together with '
                               '--details, set exit status'
                               ' to 0 iff displayed abgabe passes')
        
        self \
            .parser \
            .add_argument('-g', '--generate',
                          dest="generate",
                          action='store_true',
                          help='Generates a full .csv file with grading for moodle'
                               'and a separate .csv file for students '
                               'which passed the oral exam')

        self \
            .parser \
            .add_argument('-E', '--exam',
                          dest="oralexam",
                          nargs='*',
                          type=str,
                          default=[],
                          help='Record for a list of students that they have completed the oral exam.'
                                ' Usage: check -A "Firstname Lastname"' )

        self \
            .parser \
            .add_argument('-R', '--Revert',
                          dest="revert",
                          nargs='*',
                          type=str,
                          default=[],
                          help='Record for a list of students that they have NOT completed the oral exam. This can be used to revert an earlier operation with the -A flag.' 
                          ' Usage: check -R "Firstname Lastname"')

        self \
            .parser \
            .add_argument('-D', '--mark-manual',
                          dest="mark_manual",
                          nargs='*',
                          type=str,
                          default=[],
                          help='marks a students submission manually as passed '
                               'if corrected manually. Usage: check -D "Firstname Lastname"')

        self \
            .parser \
            .add_argument('-u', '--unpassed-students',
                          dest="unpassed",
                          action='store_true',
                          help='checks all unpassed students')


    def get_arguments(self):
        """
        getter for the parsed arguments as a dictionary
        Returns:
            parsed argsuments
        """
        return self.parser.parse_args()

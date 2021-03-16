"""
 Contains only ArgumentExtractor which encapsulates
 reading arguments from the command line
 """

import argparse


class ArgumentExtractor:
    """
    Encapsulates reading arguments from the command line
    implements:
    init_parser(self)
    get_arguments(self)
    """

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.init_parser()

    def init_parser(self):
        """
        implements the initialization of an argument parser
        if you need to read additional commandline arguments,
        please add them here!
        :return:
        """
        self \
            .parser \
            .add_argument('-f', '--fetch',
                          dest='fetch',
                          action='store_true',
                          help='fetch new submissions')
        self \
            .parser \
            .add_argument('--fetch-only',
                          dest='fetch_only',
                          action='store_true',
                          help='fetch new submissions')
        self \
            .parser \
            .add_argument('-c', '--check',
                          dest='check',
                          type=str,
                          default=[],
                          action="append",
                          help='run tests for the submissions'
                               ' of the given student')
        self \
            .parser \
            .add_argument('-a', '--all',
                          action='store_true',
                          help='run tests for all submissions')
        self \
            .parser \
            .add_argument('-t', '--test',
                          dest='test',
                          nargs='*',
                          type=str,
                          default=[],
                          help='Allows user to provide a student name and select a test to be run for their last submission.')
        self \
            .parser \
            .add_argument('-O', '--output',
                          dest="output",
                          action='store_true',
                          help='Prints output from executed sumbissions.')
        self \
            .parser \
            .add_argument('-V', '--valgrind',
                          dest="valgrind",
                          action='store_true',
                          help='Prints valgrind output from executed sumbissions.')
        self \
            .parser \
            .add_argument('-C', '--compile',
                          dest='compile',
                          type=str,
                          default='',
                          help='just compile this configuration')
        self \
            .parser \
            .add_argument('-e', '--extra',
                          nargs='*',
                          dest='extra_sources',
                          type=str,
                          default=[],
                          help='run extra tests for each submission'
                               'that has not been tested so far')
        self \
            .parser \
            .add_argument('-s', '--stats',
                          dest='stats',
                          action='store_true',
                          help='print stats only, '
                               'do test new configuration files')
        self \
            .parser \
            .add_argument('-v', '--verbose',
                          dest='verbose',
                          action='store_true',
                          help='print detailed test results'
                               ' for each test executed')
        self \
            .parser \
            .add_argument('-d', '--details',
                          nargs='*',
                          dest='details',
                          type=str,
                          default=[])
        self \
            .parser \
            .add_argument('-M', '--mail',
                          nargs='*',
                          dest='mailto',
                          type=str,
                          default=[])

        self \
            .parser.add_argument('-m', '--mail-to-all',
                                 dest='mail_to_all',
                                 action='store_true',
                                 help='send mail reports to everyone '
                                      'who has not received a report'
                                      ' for the current version yet')
        self \
            .parser. \
            add_argument('-B', '--best',
                         action='store_true',
                         help='combined with -d,'
                              ' show best submission'
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
                          action='store_true')
        self \
            .parser \
            .add_argument('-P', '--playground',
                          dest='playground',
                          action='store_true',
                          help='playground')
        self \
            .parser \
            .add_argument('--sim',
                          action='store_true',
                          help='perform all-to-all similarity check')
        self \
            .parser \
            .add_argument('--exit-status',
                          action='store_true',
                          help='if used together with '
                               '--details, set exit status'
                               ' to 0 iff displayed abgabe passes')
        self \
            .parser \
            .add_argument('--debug',
                          action='store_true',
                          help='enables sending mail only to '
                               '"C Programmierprojekt Team" moodle account')
        self \
            .parser \
            .add_argument('--force',
                          action='store_true',
                          help='forces actions like resending emails')
        self \
            .parser \
            .add_argument('-g', '--generate',
                          dest="generate",
                          action='store_true',
                          help='generates a full .csv file with grading for moodle'
                               'and a separate .csv file for students '
                               'which passed the abtestat')

        self \
            .parser \
            .add_argument('-A', '--Abtestat',
                          dest="abtestat",
                          nargs='*',
                          type=str,
                          default=[],
                          help='sets a list of students as abtestat done')

        self \
            .parser \
            .add_argument('-R', '--Revert',
                          dest="revert",
                          nargs='*',
                          type=str,
                          default=[],
                          help='reverts abtestat state for the students given')

        self \
            .parser \
            .add_argument('-D', '--mark-manual',
                          dest="mark_manual",
                          nargs='*',
                          type=str,
                          default=[],
                          help='marks a students submission manually as passed '
                               'if corrected manually')

        self \
            .parser \
            .add_argument('-u', '--unpassed-students',
                          dest="unpassed",
                          action='store_true',
                          help='checks all unpassed students')


    def get_arguments(self):
        """
        getter for the parsed arguments as a dictionary
        :return: parsed args
        """
        return self.parser.parse_args()

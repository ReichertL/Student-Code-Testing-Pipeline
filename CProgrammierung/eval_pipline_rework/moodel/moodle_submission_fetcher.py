"""
Module which implements needed functionality to
fetch submissions from local or moodle submissions
"""

import datetime
import json
import os
import re
import shutil
import subprocess
from subprocess import DEVNULL
import sys
import logging

from util.absolute_path_resolver import resolve_absolute_path
from util.colored_massages import Warn
from util.config_reader import ConfigReader
from moodel.moodle_session import MoodleSession

from alchemy.students import Student


FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)

def mkdir(path):
    """
    wrapper for creating a dir
    by just ignoring FileExistsError if thrown
    :param path: the path where the directory should be created
    :return: nothing
    """
    try:
        os.mkdir(path)
    except FileExistsError:
        pass


class MoodleSubmissionFetcher:
    """
    Implements needed functionality to
    fetch submissions from local or moodle submissions
    """

    def __init__(self, args):
        relative_config_path = "/resources/config_submission_fetcher.config"
        config_path = \
            resolve_absolute_path(relative_config_path)
        configuration = ConfigReader().read_file(config_path)
        self.configuration = configuration
        self.args = args
        relative_submission_path = self.configuration["SUBMISSION_BASE_DIR"]
        self.submission_base_dir = \
            resolve_absolute_path(relative_submission_path)
        self.moodle_session = None

    def run(self):
        """
        runs fetching functionality
        :param database_manager:
        the database manager into which new submissions should be integrated
        :return: nothing
        """
        username, session_state = self.get_login_data()
        self.moodle_session = \
            MoodleSession(username,
                          session_state,
                          self.configuration)
        self.moodle_session.update_teilnehmer()
        mkdir(self.submission_base_dir)
        self.fetch_abgaben()

    def get_login_data(self, username=None):
        """Get the desired moodle username. This can be given either by the
        environment variable MOODLE_USERNAME or as the file `./mymoodleid`.
        Otherwise the user is asked.
        """
        try:
            session_data_path = self.configuration["SESSION_DATA_PATH"]
            with open(resolve_absolute_path(session_data_path)) as f:
                d = json.load(f)
        except OSError:
            d = {}
        if username is None:
            username = os.environ.get('MOODLE_USERNAME', '')
        if not username:
            try:
                with open('mymoodleid') as f:
                    username = next(iter(f)).strip()
            except OSError:
                pass
        if not username:
            if len(self.configuration["MOODLE_OWN_USER_IDS"]) > 0:
                username = list(self.configuration["MOODLE_OWN_USER_IDS"])[0]
        if not username:
            if d:
                print('known users:')
                for k in d:
                    print(k)
            username = input('username: ')
        return username, d.get(username, {})

    def fetch_abgaben(self, dryrun=False, noimport=False):
        """
        collects all submissions from a
        specified source (moodle or local directory)
        :param database_manager:
        :param dryrun: optional no fetch from external source
        :param noimport: flag for not returning new submissions
        :return: list of new submission
        """

        new = []
        new_submissions_dir = self.configuration["SUBMISSION_NEW_DIR"]
        new_submissions_zip = self.configuration["SUBMISSION_NEW_ZIP"]
        submission_base_dir = self.configuration["SUBMISSION_BASE_DIR"]
        all_submissions_dir = resolve_absolute_path(submission_base_dir)
        use_local_zip = False
        if os.path.exists(new_submissions_zip):
            print(f'target zip path "{new_submissions_zip}" exists.\n'
                  'use local file instead of fetching? (y/n)',
                  end='', flush=True)
            answer = sys.stdin.readline()[:1]
            if answer.lower() == 'y':
                use_local_zip = True
        if not dryrun:
            if not use_local_zip:
                ms = self.moodle_session
                if not ms.logged_in:
                    return None
                with_submission_id = \
                    self.configuration["MOODLE_IDS"]["MOODLE_SUBMISSION_ID"]

                ms. \
                    download_all_submissions(with_submission_id)
            if os.path.isdir(new_submissions_dir):
                shutil.rmtree(new_submissions_dir)
            os.mkdir(new_submissions_dir)
            subprocess.call(['unzip',
                             '-d', new_submissions_dir,
                             new_submissions_zip], stdout=DEVNULL)
            os.unlink(new_submissions_zip)
        if noimport:
            return new
        dir_listing = os.listdir(new_submissions_dir)
        for d in dir_listing:
            student= self. \
                dirname_to_student(d)
            src_dir = os.path.join(new_submissions_dir, d)
            src = os.path.join(src_dir, 'loesung.c')

            if not os.path.exists(src):
                Warn('Student "{}" ({}) did not submit a source file./ The file was not named loesung.c.'.format(
                    student.name, student.id))
                continue
            dest_dir = os.path.join(all_submissions_dir, d)
            timestamp_extension = datetime \
                .datetime \
                .fromtimestamp(os.path.getmtime(src)) \
                .__str__()
            regex_timestamp = re.sub("-|:|\s", "_", timestamp_extension)

            dest = os.path.join(dest_dir, f'loesung_{regex_timestamp}.c')
            if not os.path.isdir(dest_dir):
                os.mkdir(dest_dir)

            shutil.move(src, dest)
            new.append((student.name, student.id))
        return new

    @staticmethod
    def dirname_to_student(d):
        """
        Extracts the student name and
        the submission id from a directory name
        :param d: directory name
        :param database_manager:
        the database manager from which a student is retrieved
        :return: Triple(student id, student name, submission id)
        """

        re_submission_dir = re.compile(r'(.+)_(\d+)_assignsubmission_file_')
        mo = re_submission_dir.match(d)
        student_name = mo.group(1)
        moodle_id = mo.group(2)

        student=Student.get_or_insert(student_name, moodle_id)
        return student

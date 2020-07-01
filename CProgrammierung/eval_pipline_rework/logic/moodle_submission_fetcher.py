import json
import os
import re
import shutil
import subprocess
import sys

from util.absolute_path_resolver import resolve_absolute_path
from util.colored_massages import Warn
from util.config_reader import ConfigReader
from util.moodle_session import MoodleSession


def mkdir(path):
    try:
        os.mkdir(path)
    except FileExistsError:
        pass


class MoodleSubmissionFetcher:
    def __init__(self, args):
        config_path = resolve_absolute_path("/resources/config_submission_fetcher.config")
        configuration = ConfigReader().read_file(config_path)
        self.configuration = configuration
        self.args = args
        self.submission_base_dir = resolve_absolute_path(self.configuration["SUBMISSION_BASE_DIR"])
        self.moodle_session = None

    def run(self, database_manager):
        username, session_state = self.get_login_data()
        self.moodle_session = MoodleSession(username, session_state, self.configuration, database_manager)
        self.moodle_session.update_teilnehmer(database_manager)
        mkdir(self.submission_base_dir)
        self.fetch_abgaben(database_manager)

    def get_login_data(self, username=None):
        """Get the desired moodle username. This can be given either by the
        environment variable MOODLE_USERNAME or as the file `./mymoodleid`.
        Otherwise the user is asked.
        """
        try:
            with open(resolve_absolute_path(self.configuration["SESSION_DATA_PATH"])) as f:
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

    def fetch_abgaben(self, database_manager, dryrun=False, noimport=False):
        new = []
        new_submissions_dir = self.configuration["SUBMISSION_NEW_DIR"]
        new_submissions_zip = self.configuration["SUBMISSION_NEW_ZIP"]
        all_submissions_dir = resolve_absolute_path(self.configuration["SUBMISSION_BASE_DIR"])
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
                ms.download_all_submissions(self.configuration["MOODLE_IDS"]["MOODLE_SUBMISSION_ID"])
            if os.path.isdir(new_submissions_dir):
                shutil.rmtree(new_submissions_dir)
            os.mkdir(new_submissions_dir)
            subprocess.call(['unzip',
                             '-d', new_submissions_dir,
                             new_submissions_zip])
            os.unlink(new_submissions_zip)
        if noimport:
            return new
        dir_listing = os.listdir(new_submissions_dir)
        for d in dir_listing:
            student_id, student_name, submission_id = self.dirname_to_student(d, database_manager)
            src_dir = os.path.join(new_submissions_dir, d)
            src = os.path.join(src_dir, 'loesung.c')

            if not os.path.exists(src):
                Warn('Student "{}" ({}) did not submit a source file.'.format(
                    student_name, student_id))
                continue
            dest_dir = os.path.join(all_submissions_dir, d)
            dest = os.path.join(dest_dir, 'loesung.c')
            if os.path.isdir(dest_dir):
                assert os.path.exists(dest)
                if os.path.getmtime(src) == os.path.getmtime(dest):
                    continue
                for i in range(1, 100):
                    bak = dest[:-2] + '-{:02d}.c'.format(i)
                    if not os.path.exists(bak):
                        break
                assert not os.path.exists(bak)
                os.rename(dest, bak)
                print(dest)
                print(bak)
            else:
                os.mkdir(dest_dir)
            shutil.move(src, dest)
            new.append((student_id, student_name))
        # if not dryrun:
        #     shutil.rmtree(new_submissions_dir)
        return new

    @staticmethod
    def dirname_to_student(d, database_manager):
        re_submission_dir = re.compile(r'(.+)_(\d+)_assignsubmission_file_')
        mo = re_submission_dir.match(d)
        student_name = mo.group(1)
        student_id = database_manager.get_student_by_name(student_name)
        submission_id = mo.group(2)
        return student_id, student_name, submission_id

"""
implements emailing automatization and capabilities
"""

import os
import subprocess
import sys
from datetime import datetime

from logic.moodle_submission_fetcher import MoodleSubmissionFetcher
from logic.result_generator import ResultGenerator
from util.absolute_path_resolver import resolve_absolute_path
from util.config_reader import ConfigReader
from util.moodle_session import MoodleSession


class MoodleReporter:
    """
    class responsible for automatically create and send e-mail to students
    """
    dump_generator = ResultGenerator()

    def __init__(self, args):
        """
        Constructor creates a MoodleReporter instance
        based on given arguments which determine the behaviour
        :param args: given commandline arguments
        """
        self.args = args
        config_path = resolve_absolute_path(
            "/resources/config_submission_fetcher.config")
        configuration = ConfigReader().read_file(config_path)
        self.configuration = configuration
        self.moodle_session = None

    @staticmethod
    def get_fail_information_snippet(failed_description, mail_templates):
        """
        Generates an email part which gives information about
        the failed properties of the submission in HTML
        :param failed_description: describes the failed aspects
        of the submission
        :param mail_templates: the text building blocks
        :return: failure text
        """
        failed_snippet = ""
        if len(failed_description) > 0:
            failed_snippet = '<p>\n'
            for error_type in failed_description:
                failed_snippet += f"{mail_templates[error_type]} "
                failed_cases = failed_description[error_type]
                if len(failed_cases) == 1:
                    failed_snippet += f"{failed_cases[0]}.\n"
                else:
                    failed_snippet += "\n"
                    failed_snippet += '<ul>\n'

                    for hint, dot in zip(failed_cases,
                                         (len(failed_cases) - 1)
                                         * ('',) + ('.',)):
                        failed_snippet += f'<li>{hint}{dot}</li>\n'

                    failed_snippet += '</ul>\n'
            failed_snippet += '</p>\n'

        return failed_snippet

    def generate_mail_content(self, student, submission):
        """
        generates the mail itself
        for a given student and submission
        :param student: the respective student
        :param submission: the respective submission
        :return: the email string as HTML
        """
        mail_templates = {}
        for root, _, files in os.walk(
                self.configuration["MAIL_TEMPLATE_DIR"]
                ,
                topdown=False):
            for file in files:
                path = os.path.join(root + os.path.sep + file)
                identifier = file.replace(".mail", "")
                text = ""
                with open(path, "r") as content:
                    text = text.join(content.readlines())
                mail_templates.update({identifier: text})

        mail = mail_templates["greeting"].replace("$name$", student.name)
        if submission.passed:
            if self.args.final:
                mail += mail_templates["successful_final"]
            else:
                mail += mail_templates["successful"]
        else:
            if submission.compilation is not None and submission.compilation:
                bad_failed_description = {}
                good_failed_description = {}
                for i in submission.tests_bad_input:
                    if not i.passed():
                        bad_failed_description = i \
                            .get_failed_description(bad_failed_description)
                for i in submission.tests_good_input:
                    if not i.passed():
                        good_failed_description = i \
                            .get_failed_description(good_failed_description)

                good_failed_snippet = mail_templates["good_test_failed_intro"]
                if len(bad_failed_description) > 0:
                    mail += mail_templates["bad_test_failed_intro"]
                    good_failed_snippet = \
                        good_failed_snippet \
                            .replace("$also_token$", "Auch wenn")
                    mail += self. \
                        get_fail_information_snippet(bad_failed_description,
                                                     mail_templates)

                if len(good_failed_description) > 0:
                    mail += good_failed_snippet.replace("$also_token$", "Wenn")
                    mail += self. \
                        get_fail_information_snippet(good_failed_description,
                                                     mail_templates)

            else:
                if submission.compilation is not None:
                    mail += mail_templates["not_compiled"] \
                        .replace("$commandline$",
                                 submission.compilation.commandline) \
                        .replace("$compilation_output$",
                                 submission.compilation.output)
                else:
                    print(f"--{student.name}'s submission was not compiled "
                          f"before mailing him--")
                if not self.args.final:
                    mail += mail_templates["not_compiled_hint"]

            if not self.args.final:
                mail += mail_templates["further_attempts"]
            else:
                if student.passed:
                    mail += mail_templates["extra_passed_final"]
                else:
                    mail += mail_templates["not_passed_final"]
        mail += mail_templates["ending"] \
            .replace("$submission_timestamp$",
                     datetime.fromtimestamp(submission.mtime)
                     .strftime('%d.%m.%Y, %T Uhr'))

        if not self.args.final:
            mail += mail_templates["automatically_generated"]
        mail += "\n"
        return mail

    def send_mail(self, student, submission, text):
        """
        Interaction for sending a mail with regards to
        corrector interaction
        :param student: the respective student
        :param submission: the respective submission
        :param text: the HTML String
        :return: boolean whether the sending
        was successful
        """
        success = False
        stats_path = 'stats'
        text_path = "text"
        with open(stats_path, 'w') as f:
            submission.print_stats(f)
        with open(text_path, 'w') as f:
            f.write(text)

        editor = ""
        try:
            editor = self.configuration["EDITOR_PATH"]
        except KeyError:
            editor = ""

        try:
            if len(os.environ["EDITOR"]) > 0:
                editor = os.environ["EDITOR"]
        except KeyError:
            pass
        if len(editor) == 0:
            print("No editor specified")
        while True:
            subprocess.call(f'/bin/cat "{text_path}" "{stats_path}" | less -R',
                            shell=True)
            print(
                f'To {student.name}  '
                'send this mail? (y/n/m/e/v/o/q) '
                'y=send; '
                'n=do not send; '
                'm=mark as mailed anyways'
                'e=edit mail; '
                'v=view source code; '
                'o = open conversation in browser; '
                'q = quit ',
                end='', flush=True)

            answer = sys.stdin.readline()[0]
            if answer == 'e':
                if not len(editor) == 0:
                    subprocess.call([editor, text_path])
            elif answer == 'v':
                if not len(editor) == 0:
                    subprocess.call([editor, submission.path])
            elif answer == 'o':
                self.moodle_session.open_conversation_in_ff(student.moodle_id)
            elif answer == 'm':
                success = True
                break
            elif answer == 'q':
                os.unlink(text_path)
                os.unlink(stats_path)
                sys.exit(0)
            elif answer == 'y':
                with open(text_path) as f:
                    msg = f.read()
                success = self.moodle_session. \
                    send_instant_message(student.moodle_id, msg)
                break
            elif answer == 'n':
                break
            else:
                continue

        os.unlink(text_path)
        os.unlink(stats_path)
        return success

    def run(self, database_manager, force=False):
        """
        Iteration over all students
        which haven't received an e-mail yet
        :param database_manager: database manager
        to retrieve necessary information
        regarding unmailed students and their submission
        :param force: boolean enforces remailing
        :return: nothing
        """
        username, session_state = MoodleSubmissionFetcher(self.args). \
            get_login_data()
        self.moodle_session = MoodleSession(username,
                                            session_state,
                                            self.configuration,
                                            database_manager)
        to_mail = []

        if self.args.mail_to_all:
            if self.args.verbose:
                print("Mailing everybody who hasn't "
                      "received a mail for the latest submission yet")
            to_mail = database_manager.get_all_students()
        if len(self.args.mailto) > 0:
            for student_name in self.args.mailto:
                to_mail.append(database_manager.
                               get_student_by_name(student_name))

        if self.args.debug:
            to_mail = []
            to_mail.append(database_manager.
                           get_student_by_name("C Programmierprojekt Team"))

        for student in to_mail:
            submissions = database_manager.get_submissions_for_student(student)
            if len(submissions) > 0:
                submissions = sorted(
                    submissions, key=lambda x: x.timestamp
                )

                mail_information = database_manager. \
                    get_mail_information(student
                                         , submissions[-1])
                already_mailed = False

                if mail_information is not None:
                    if mail_information.time_stamp is not None:
                        if self.args.verbose and \
                                (self.args.rerun or self.args.force):
                            print(f"Already send a mail to {student.name} "
                                  f"at {mail_information.time_stamp}")
                        already_mailed = True
                        if self.args.verbose and \
                                (self.args.rerun or self.args.force):
                            print('Send anyway? (y/n) ', end='', flush=True)
                            if sys.stdin.readline()[:1] == 'y':
                                already_mailed = False

                if (not already_mailed) or self.args.force:
                    if self.args.verbose:
                        print(f"Sending mail to {student.name}, "
                              f"mailed at {datetime.now()}")
                    submission = submissions[-1]
                    text = self.generate_mail_content(student, submission)
                    success = self.send_mail(student, submission, text)
                    if success:
                        if student.passed:
                            self.dump_generator.add_line(student, 1)
                        database_manager.insert_mail_information(student
                                                                 , submission
                                                                 , text)
        self.dump_generator.dump_list()

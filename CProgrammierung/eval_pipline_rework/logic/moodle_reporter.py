import os
from datetime import datetime

from logic.moodle_submission_fetcher import MoodleSubmissionFetcher
from util.absolute_path_resolver import resolve_absolute_path
from util.config_reader import ConfigReader
from util.moodle_session import MoodleSession


class MoodleReporter:

    def __init__(self, args):
        self.args = args
        config_path = resolve_absolute_path("/resources/config_submission_fetcher.config")
        configuration = ConfigReader().read_file(config_path)
        self.configuration = configuration
        self.moodle_session = None

    def generate_mail_content(self, student, submission):
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
                bad_failed = False
                good_failed = False
                failed_description = {}
                for i in submission.tests_bad_input:
                    if not i.passed():
                        bad_failed = True
                        failed_description = i.get_failed_description(failed_description)
                for i in submission.tests_good_input:
                    if not i.passed():
                        good_failed = True
                        failed_description = i.get_failed_description(failed_description)

                good_failed_snippet = mail_templates["good_test_failed_intro"]
                if bad_failed:
                    mail += mail_templates["bad_test_failed_intro"]
                    good_failed_snippet=good_failed_snippet.replace("$also_token$", "Auch wenn")

                if good_failed:
                    mail += good_failed_snippet.replace("$also_token$", "Wenn")

                if len(failed_description.keys()) > 0:
                    failed_snippet = '<p>\n'
                    if len(failed_description) == 1:
                        for key in failed_description:
                            failed_snippet += f"{mail_templates[failed_description[key]]}\n"

                    else:
                        failed_snippet += '<ul>\n'
                        for i in failed_description:
                            failed_snippet += f'<li>{mail_templates[failed_description[i]]}</li>\n'

                        failed_snippet += '</ul>\n'
                    failed_snippet += '</p>\n'
                mail += failed_snippet
            else:
                if submission.compilation is not None:
                    mail += mail_templates["not_compiled"] \
                        .replace("$commandline$", submission.compilation.commandline) \
                        .replace("$compilation_output$", submission.compilation.output)
                else:
                    print(f"--{student.name}'s submission was not compiled before mailing him--")
                if not self.args.final:
                    mail += mail_templates["not_compiled_hint"]

            if not self.args.final:
                mail += mail_templates["further_attempts"]
            else:
                if student.passed:
                    mail += mail_templates["extra_passed_final"]
                else:
                    mail += mail_templates["not_passed_final"]

        mail += mail_templates["ending"].replace("$submission_timestamp$", str(submission.timestamp))

        if not self.args.final:
            mail += mail_templates["automatically_generated"]
        print()
        print(mail)
        print()
        return mail

    def send_mail(self, student, text):
        pass

    def run(self, database_manager, force=False):
        username, session_state = MoodleSubmissionFetcher(self.args).get_login_data()
        self.moodle_session = MoodleSession(username, session_state, self.configuration, database_manager)
        to_mail = []

        if self.args.mail_to_all:
            if self.args.verbose:
                print("Mailing everybody who hasn't received a mail for the latest submission yet")
            to_mail = database_manager.get_all_students()
        if len(self.args.mailto) > 0:
            for student_name in self.args.mailto:
                to_mail.append(database_manager.get_student_by_name(student_name))
        for student in to_mail:
            submission = database_manager.get_submissions_for_student(student)
            if len(submission) > 0:
                submission = sorted(
                    submission, key=lambda x: x.timestamp
                )
                mail_information = database_manager.get_mail_information(student, submission[-1])
                already_mailed = False

                if mail_information is not None:
                    if mail_information.time_stamp is not None:
                        print(f"Already send a mail to {student.name} at {mail_information.time_stamp}")
                        already_mailed = True

                if not already_mailed or force:
                    if self.args.verbose:
                        print(f"Sending mail to {student.name}, mailed at {datetime.now()}")
                    text = self.generate_mail_content(student, submission[-1])
                    success = self.send_mail(student, text)
                    if success:
                        database_manager.insert_mail_information(student, submission, text)

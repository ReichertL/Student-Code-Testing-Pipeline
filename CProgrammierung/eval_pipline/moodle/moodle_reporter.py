"""
This module implements the sending of notifications to students via Moodle.
"""

import os
import subprocess
import sys
from datetime import datetime
import logging
from moodle.moodle_submission_fetcher import MoodleSubmissionFetcher
from logic.result_generator import ResultGenerator
from util.absolute_path_resolver import resolve_absolute_path
from util.config_reader import ConfigReader
from util.select_option import select_option_interactive
from moodle.moodle_session import MoodleSession
from database.submissions import Submission
from database.students import Student
from database.runs import Run
from database.testcase_results import TestcaseResult
import database.database_manager as dbm

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)


class MoodleReporter:
    """
    Class responsible for automatically create and send e-mail to students
    """
    dump_generator=ResultGenerator()

    def __init__(self, args):
        """
        Constructor creates a MoodleReporter instance
        based on given commandline arguments and a configuration file  which determine the behaviour.
        Parameters:
            args (ArgumentParser object): commandline arguments
        """
        self.args=args
        config_path=resolve_absolute_path(
            "/resources/config_submission_fetcher.config")
        configuration=ConfigReader().read_file(config_path)
        self.configuration=configuration
        self.moodle_session=None

    def run(self):
        """
        Sends message to students using the commandline arguments.
        If mail_to_all is set, everyone who has not received a message for their submission yet will be sent one.
        If the -M flag was used, messages can be sent to only a handful of people.
        If the -r flag is used, mails can be sent even if the student has already received a mail for this submission.
        Messages that have been sent are saved to a log file.
        Parameters: None
        Returns: Nothing
        """
        username, session_state=MoodleSubmissionFetcher(self.args). \
            get_login_data()
        self.moodle_session=MoodleSession(username,
                                          session_state,
                                          self.configuration)
        to_mail=[]

        if self.args.mail_to_all:
            if self.args.verbose:
                logging.info("Mailing everybody who hasn't "
                             "received a mail for the latest submission yet")
            to_mail=Submission.get_submissions_for_notification()

        if len(self.args.mailto)>0:
            for name in self.args.mailto:

                student=Student.get_student_by_name(name)
                if type(student)==list:
                    student=select_option_interactive(student)
                if not self.args.mail_manual:
                    sub, stud=Submission.get_last_for_name(student.name)
                else:
                    pairs=Submission.get_all_for_name(student.name)
                    sub, stud=select_option_interactive(pairs)
                to_mail.append([stud, sub])
        else:
            logging.info("No Mails to send")

        sorted_to_mail=sorted(to_mail, key=lambda pair: (pair[0].name, pair[1].submission_time))
        for student, submission in sorted_to_mail:
            if submission.student_notified is True and self.args.rerun:
                print(f"Already send a mail to {student.name} "
                      f"at {submission.notification_time}")
                print('Send anyway? (y/n) ', end='', flush=True)
                if sys.stdin.readline()[:1]!='y':
                    continue

                if self.args.verbose:
                    print(f"Sending mail to {student.name}, "
                          f"mailed at {datetime.now()}")
            elif submission.student_notified:
                continue

            run=Run.get_last_for_submission(submission)
            text=self.generate_mail_content(student, submission, run)
            success=self.send_mail(student, submission, run, text, student.grade)
            if success:
                if run.passed:
                    self.dump_generator.add_line(student)
                self.write_to_mail_log(student, submission, text)
                submission.notification_time=datetime.now()
                submission.student_notified=True
                dbm.session.commit()
        self.dump_generator.dump_list()

    def send_mail(self, student, submission, run, text, grade=None):
        """
        Mails are sent automatically unless the -U flag is set.
        It allows user interaction before sending a mail such as editing the mail.
        Parameters:
            student (Student object): the respective student
            submission (Submission object): the respective submission
            run (Run object): the respective run
            text (string): the HTML String
            grade: optional grade for the specific student. Default: None.

        Returns:
            Boolean whether the sending was successful
        """
        success=False
        stats_path='stats'
        text_path="text"
        if run is not None:
            with open(stats_path, 'w') as f:
                ResultGenerator.print_stats(run, f)
        with open(text_path, 'w') as f:
            f.write(text)
            f.write(
                "------------------------------------------------------------------------------------------------------------------------------------------")

        if not self.args.mail_manual:
            with open(text_path) as f:
                msg=f.read()
                success=self.moodle_session. \
                    send_instant_message(student.moodle_id, msg)
                if success:
                    logging.info(f"successfully sent message to {student.name}")
                    if grade is not None:
                        self.moodle_session \
                            .update_grading(student.moodle_id, grade)
                        student.grade=grade
                        dbm.session.commit()
                else:
                    logging.error(f"Failed to send message to {student.name}")

        else:
            try:
                editor=self.configuration["EDITOR_PATH"]
            except KeyError:
                editor=""

            try:
                if len(os.environ["EDITOR"])>0:
                    editor=os.environ["EDITOR"]
            except KeyError:
                pass
            if len(editor)==0:
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

                answer=sys.stdin.readline()[0]
                if answer=='e':
                    if not len(editor)==0:
                        subprocess.call([editor, text_path])
                elif answer=='v':
                    if not len(editor)==0:
                        subprocess.call([editor, submission.path])
                elif answer=='o':
                    self.moodle_session.open_conversation_in_ff(student.moodle_id)
                elif answer=='m':
                    success=True
                    break
                elif answer=='q':
                    os.unlink(text_path)
                    os.unlink(stats_path)
                    sys.exit(0)
                elif answer=='y':
                    with open(text_path) as f:
                        msg=f.read()
                    success=self.moodle_session. \
                        send_instant_message(student.moodle_id, msg)
                    if success:
                        if grade is None:
                            gr=input('set grade in moodle? (0/1/2) ')
                            if gr in ('0', '1', '2'):
                                grade=int(gr)
                        if grade is not None:
                            self.moodle_session \
                                .update_grading(student.moodle_id, grade)
                            print('INFO: updated moodle grade to {}'.format(grade))
                            student.grade=grade
                            dbm.session.commit()

                    break
                elif answer=='n':
                    break
                else:
                    continue

        os.unlink(text_path)
        os.unlink(stats_path)
        return success

    def generate_mail_content(self, student, submission, run):
        """
        Generates a notification mail for a given student and submission.
        Parameters:
            student: the respective student
            submission: the respective submission
            run: the respective run
        Returns:
            The mail as string containing HTML
        """
        mail_templates={}
        mail_template_path=resolve_absolute_path(self.configuration["MAIL_TEMPLATE_DIR"])
        for root, _, files in os.walk(mail_template_path, topdown=False):
            for file in files:
                path=os.path.join(root+os.path.sep+file)
                identifier=file.replace(".mail", "")
                text=""
                with open(path, "r") as content:
                    text=text.join(content.readlines())
                mail_templates.update({identifier: text})
        mail=mail_templates["greeting"].replace("$name$", student.name)
        if run.passed:
            if self.args.final:
                mail+=mail_templates["successful_final"]
            else:
                mail+=mail_templates["successful"]
        else:
            if run.compilation_return_code==0:
                bad_failed_desc={}
                good_failed_desc={}
                bad_or_out_failed_desc={}

                failed_bad=TestcaseResult.get_failed_bad(run)
                failed_bad.sort(key=lambda x: x[1].short_id)
                for result, testcase, valgrind in failed_bad:
                    bad_failed_desc=self.get_failed_description(result, testcase, valgrind, bad_failed_desc)

                failed_good=TestcaseResult.get_failed_good(run)
                failed_good.sort(key=lambda x: x[1].short_id)
                for result, testcase, valgrind in failed_good:
                    good_failed_desc=self.get_failed_description(result, testcase, valgrind, good_failed_desc)

                failed_bad_or_out=TestcaseResult.get_failed_output_bad_or_output(run)
                failed_bad_or_out.sort(key=lambda x: x[1].short_id)
                for result, testcase in failed_bad_or_out:
                    bad_or_out_failed_desc=self.get_failed_description(result, testcase, valgrind,
                                                                       bad_or_out_failed_desc)

                if len(bad_failed_desc)>0:
                    mail+=mail_templates["bad_test_failed_intro"]
                    mail+=self. \
                        get_fail_information_snippet(bad_failed_desc,
                                                     mail_templates)
                if len(bad_or_out_failed_desc)>0:
                    mail+=mail_templates["bad_or_output_test_failed_intro"]
                    mail+=self. \
                        get_fail_information_snippet(bad_or_out_failed_desc,
                                                     mail_templates)

                if len(good_failed_desc)>0:
                    good_failed_snippet=mail_templates["good_test_failed_intro"]
                    token="Wenn"
                    if len(bad_failed_desc)>0 or len(bad_or_out_failed_desc)>0:
                        token="Auch wenn"
                    mail+=good_failed_snippet.replace("$also_token$", token)
                    mail+=self. \
                        get_fail_information_snippet(good_failed_desc, mail_templates)

            elif run.compilation_return_code!=0:
                mail+=mail_templates["not_compiled"] \
                    .replace("$commandline$", run.command_line) \
                    .replace("$compilation_output$", run.compiler_output)
                if not self.args.final:
                    mail+=mail_templates["not_compiled_hint"]
            else:
                logging.warning(f"--{student.name}'s submission was not compiled "
                                f"before mailing him--")

            if not self.args.final:
                mail+=mail_templates["further_attempts"]
            else:
                if Student.is_student_passed(student.name):
                    mail+=mail_templates["extra_passed_final"]
                else:
                    mail+=mail_templates["not_passed_final"]
        mail+=mail_templates["ending"] \
            .replace("$submission_timestamp$",
                     submission.submission_time
                     .strftime('%d.%m.%Y, %T Uhr'))

        if not self.args.final:
            mail+=mail_templates["automatically_generated"]
        mail+="\n"
        return mail

    @staticmethod
    def get_fail_information_snippet(failed_description, mail_templates):
        """
        Generates an email part which gives information about
        the failed properties of the submission in HTML.
        Parameters:
            failed_description (json): for different error types (e.g. Valgrind, timeout...)
                it contains a list of testcases which produced this error
            mail_templates (dict): the text building blocks

        Returns:
            String containing the description using HTML for formatting
        """
        failed_snippet=""
        if len(failed_description)>0:
            failed_snippet='<p>\n'
            for error_type in failed_description:
                failed_snippet+=f"{mail_templates[error_type]} "
                failed_cases=failed_description[error_type]
                if len(failed_cases)==1:
                    failed_snippet+=f"{failed_cases[0]}.\n"
                else:
                    failed_snippet+="\n"
                    failed_snippet+='<ul>\n'

                    for hint, dot in zip(failed_cases,
                                         (len(failed_cases)-1)
                                         *('',)+('.',)):
                        failed_snippet+=f'<li>{hint}{dot}</li>\n'

                    failed_snippet+='</ul>\n'
            failed_snippet+='</p>\n'

        return failed_snippet

    def get_failed_description(self, result, testcase, valgrind, description=None):
        """
        For a testcase result and a testcase this functions generates  or updates
        a dict.
        This dict contains for different error types a list of testcases for which the corresponding submission failed,
        which produced this error.
        Error types are  timeout, segfault, wrong return code, valgrind leak, valgrind write error, valgrind read
        error, wrong output and no error message.

        Parameters:
            result (TestcaseResult object): the results from running the testcase for a solution
            testcase (Testcase object): the testcase for which the description is created or updated
            valgrind (ValgrindOutput object): the corresponding Valgrind output (if applicable)
            description(json): can be passed to update an existing description

        Returns:
            description (dict) updated for the given key using information from the testcase
        """
        if description is None:
            description={}
        if result.timeout:
            self.append_self(testcase, description, "timeout")

        if result.timeout and result.segfault:
            self.append_self(testcase, description, "segfault")

        if not result.returncode_correct(testcase=testcase):
            self.append_self(testcase, description, "return_code")

        if valgrind is not None:

            if not valgrind.ok:
                if valgrind.invalid_read_count>0:
                    self.append_self(testcase, description, "valgrind_read")

                if valgrind.invalid_write_count>0:
                    self.append_self(testcase, description, "valgrind_write")

                if valgrind.definitely_lost_bytes!=(0 or None):
                    self.append_self(testcase, description, "valgrind_leak")
                elif valgrind.possibly_lost_bytes!=(0 or None):
                    self.append_self(testcase, description, "valgrind_leak")
                elif valgrind.indirectly_lost_bytes!=(0 or None):
                    self.append_self(testcase, description, "valgrind_leak")
                elif valgrind.still_reachable_bytes!=(0 or None):
                    self.append_self(testcase, description, "valgrind_leak")

        if testcase.type=="BAD":
            if result.error_msg_quality<1:
                self.append_self(testcase, description, "error_massage")
        else:
            if not result.output_correct and not result.timeout:
                self.append_self(testcase, description, "output")
        return description

    def append_self(self, testcase, description, key):
        """
        Generates partial sentences for failed tests and testcases and updates the corresponding list in description.
        Parameters:
            testcase (Testcase object): testcase for which the error occurred
            description (dict) ; description of errors organised by error type
            key (string): error type, so the correct list can be updated
        Returns
            description (dict) updated for the given key using information from the testcase
        """
        update_list=[]
        if key in description:
            update_list=description[key]
        if len(testcase.hint)>0:
            update_list.append(testcase.hint)
        else:
            update_list.append(f"bei {testcase.short_id}")
        description.update({key: update_list})

    def update_grade_on_moodle(self, student, grade):
        """
        This function updates a students grade on moodle for the programming exercise.
        Parameters:
            student (Student object): the student in question
            grade (int): the new grade
        Returns: Nothing
        """
        username, session_state=MoodleSubmissionFetcher(self.args).get_login_data()
        self.moodle_session=MoodleSession(username,
                                          session_state,
                                          self.configuration)
        self.moodle_session.update_grading(student.moodle_id, grade)

    def write_to_mail_log(self, student, submission, text):
        """
        Writes mails to a log file. This function is called after the mail has been sent.
        Parameters:
            student (Student object); the student which received the mail
            submission (Submission object): the submission for which the mail was sent out
            text (string); Mail text that was sent to the student
        Returns; Nothing
        """
        path=resolve_absolute_path(self.configuration["MAIL_LOG"])
        with open(path, "a+") as mail_log:
            mail_log.write(str(datetime.now())+" Mail sent to "+str(student.name)+"for submission from the "+str(
                submission.submission_time)+". The sent mail was: \n"+str(text))
            
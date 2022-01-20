"""
    Module to implement needed functionality to generate all
    statistics and summaries.
"""
import csv
import datetime
import sys
import logging
from database.students import Student
from database.submissions import Submission
from database.runs import Run
from database.testcase_results import TestcaseResult
from database.testcases import Testcase
from util.colored_massages import red, yellow, green
from util.htable import table_format
from util.select_option import select_option_interactive

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


class ResultGenerator:
    """
    Class to implement needed functionality to generate all
    statistics and summaries.
    """

    to_dump_list=[]

    def __init__(self):
        self.csv_path="moodle_result_dump.csv"
        self.csv_mailed_path="moodle_success_mailed_dump.csv"
        self.oralexam_done_path="oralexam_done_dump.csv"
        self.to_dump_list.append(["ID", "Name", "Score"])

    def generate_csv_dump(self, ):
        """
        Generates all necessary csv-files.
        One file which provides information about students who submitted a solution that passed all testcases.
        The second file only contains information about students who also passed the oral exam.
        Timestamps are printed in iso format.
        :return:nothing
        """

        passed_students=Student.get_students_passed()
        with open(self.csv_path, "w", encoding='utf-8') as result_file:
            result_writer=csv.writer(result_file, delimiter=";")
            header=["ID", "Name", "Score"]
            result_writer.writerow(header)
            for s in passed_students:
                row=[s.uni_id, s.name, s.grade]
                result_writer.writerow(row)

        with open(self.oralexam_done_path, "w") as result_file:
            result_writer=csv.writer(result_file, delimiter=";")

            oralexam_done=Student.get_oralexam_done()
            if len(oralexam_done)>0:
                header=["Name", "UniID", "Timestamp"]
                result_writer.writerow(header)
                for s in oralexam_done:
                    row=[s.name,
                         s.uni_id,
                         s.oralexam_time.strftime("%Y-%m-%d %H:%M:%S")]
                    result_writer.writerow(row)

    @staticmethod
    def print_summary_stats_small(args):
        """
        Prints summarized stats for all students that have at least  one submission which has been checked.
        Parameters:
            args (ArgumentParser object): contains the commandline arguments
        Returns: Nothing
        """
        if args.unpassed:
            students=Student.get_students_not_passed()
            # logging.debug(students)
        else:
            students=Student.get_students_all()
        for student in students:
            sub_stud=Submission.get_all_for_name(student.name)
            if len(sub_stud)>0:
                print(f"Stats for {student.name}")
            for submission, _ in sub_stud:
                if submission.is_checked:
                    print(f"Submission from the {submission.submission_time}")
                    run=Run.get_last_for_submission(submission)
                    ResultGenerator.print_small_stats(run, sys.stdout)

    def add_line(self, student):
        """
        Adds a line to the list of students that should be contained in the csv result dump.
        Parameters:
            student (Student object): the student entity
        Returns: Nothing
        """
        row=[student.uni_id, student.name, student.grade]
        self.to_dump_list.append(row)

    def dump_list(self):
        """
        Creates a csv list for all students who have received a mail and places it in a predefined location.
        Parameters: None
        Returns: Nothing
        """
        if len(self.to_dump_list)>1:
            with open(self.csv_mailed_path, "w") as result_file:
                result_writer=csv.writer(result_file, delimiter=",")
                for i in self.to_dump_list:
                    result_writer.writerow(i)

    def print_details(self, names):
        """
        Prints detailed information regarding the last submission for a list of names in detail to the console.
        Parameters:
            names (list of Strings): A list of student names
        Returns: Nothing
        """
        for name in names:
            student=Student.get_student_by_name(name)
            if student is None:
                print(f"No student with this name {name} found!")
                continue
            elif type(student)==list:
                student=select_option_interactive(student)
                name=student.name
            print(f"Printing details for {name}:")
            sub_stud=Submission.get_all_for_name(name)
            if len(sub_stud)>1:
                print("More than one submission found. Please select!")
                for index, pair in zip(range(0, len(sub_stud)), sub_stud):
                    submission, student=pair
                    print(f"[{index+1}]: {submission.submission_time}")

                answer_accepted=False
                answer=0
                while not answer_accepted:
                    answer=sys.stdin.readline()
                    try:
                        answer=int(answer)-1
                        if len(sub_stud)>answer>=0:
                            answer_accepted=True
                        else:
                            print(f"{answer+1} is not in range of"
                                  f"[{1},{len(sub_stud)}],"
                                  f"please select again!")
                    except ValueError:
                        print(f"{answer} is not a number,"
                              f"please select again!")

                run=Run.get_last_for_submission(sub_stud[answer][0])
                self.print_stats(run, sys.stdout)

            elif len(sub_stud)==1:
                run=Run.get_last_for_submission(sub_stud[0][0])
                self.print_stats(run, sys.stdout)

            else:
                print("No submissions for this student found!")

    @classmethod
    def print_small_stats(cls, run, f):
        """
        Print for a run the rough information about the number of failed and passed testcases.
        If  f=sys.stdout is used, then the lines are printed to the console.
        Parameters:
            run (Run object): Contains information about the execution of a submission
            f : File descriptor or Pipe
        Returns: Nothing
        """
        output=''
        if run.compilation_return_code!=0:
            output=output+(red('Compilation failed. '))
            print(output)
            return

        output=output+(green('Compilation successful. '))

        failed_bad=len(TestcaseResult.get_failed_bad(run))
        failed_good=len(TestcaseResult.get_failed_good(run))

        if run.passed and run.manual_overwrite_passed:
            failed_bad=0
            failed_good=0
            print(f'This run was manually marked as passed (run.id={run.id})')

        failed_bad=len(TestcaseResult.get_failed_bad(run))
        all=len(Testcase.get_all_bad())
        if failed_bad>0:
            output=output+(red(f'{failed_bad} / {all} bad tests failed. '))
        else:
            output=output+(green(f'0 / {all} bad tests failed. '))

        all=len(Testcase.get_all_good())
        if failed_good>0:
            output=output+(red(f'{failed_good} / {all} good tests failed. '))
        else:
            output=output+(green(f'0 / {all} good tests failed. '))

        print(output, file=f)

    @classmethod
    def print_stats(cls, run, f):
        """
        Print for a run the exact information regarding failed and passed testcases.
        Shows valgrind infos, segfaults, timeouts, return codes, whether the output was as expected
        and if applicable the description of the error.
        If  f=sys.stdout is used, then the lines are printed to the console.
        Parameters:
            run (Run object): Contains information about the execution of a submission
            f : File descriptor or Pipe
        Returns: Nothing
        """
        hline="------------------------------------------------------------------------"
        if run.compilation_return_code!=0:
            print(red('compilation failed; compiler errors follow:'), file=f)
            print(hline, file=f)
            print(run.command_line, file=f)
            print(run.compiler_output, file=f)
            print(hline, file=f)
            return
        if len(run.compiler_output)>0:
            print(yellow('compilation produces the following warnings:'), file=f)
            print(hline, file=f)
            print(run.command_line, file=f)
            print(run.compiler_output, file=f)
            print(hline, file=f)

        failed_bad=TestcaseResult.get_failed_bad(run)
        failed_good=TestcaseResult.get_failed_good(run)

        if run.passed and run.manual_overwrite_passed:
            failed_bad=[]
            failed_good=[]
            print(f'This run was manually marked as passed (run.id={run.id})')

        if len(failed_bad)==0 and run.compilation_return_code==0:
            print(green('All tests concerning malicious input passed.'), file=f)
        else:
            all=len(Testcase.get_all_bad())
            print(red(f'{len(failed_bad)} / {all} tests concerning malicious input failed.')
                  , file=f)
            print(file=f)
            failed_bad.sort(key=lambda x: x[1].short_id)
            print(table_format(
                '{id} | {valgrind} | {valgrind_rw} | {segfault} | {timeout} | {return} | {output} | {error_description}',
                cls.create_stats(failed_bad),
                titles='auto'), file=f)
            print(file=f)

        if len(failed_good)==0 and run.compilation_return_code==0:
            print(green('All tests concerning good input passed.'), file=f)
        else:
            all=len(Testcase.get_all_good())
            print(red(f'{len(failed_good)} / {all} tests concerning good input failed.')
                  , file=f)
            print(file=f)
            failed_good.sort(key=lambda x: x[1].short_id)
            print(table_format(
                '{id} | {valgrind} | {valgrind_rw} | {segfault} | {timeout} | {return} | {output} | {error_description}',
                cls.create_stats(failed_good),
                titles='auto'), file=f)
            print(file=f)
        if run.passed and run.manual_overwrite_passed:
            print(green("This run passed. It was marked manually."))
        elif run.passed:
            print(green("This run passed."))
        else:
            print(red("This run did not pass."))

    @classmethod
    def print_stats_testcase_result(cls, tc_result, tc, valgrind):
        """
        Prints exact information about the execution of a specific testcase for a specific run to the console.
        Shows valgrind infos, segfaults, timeouts, return codes, whether the output was as expected
        and if applicable the description of the error.

        Parameters:
            tc_result (TestcaseResult object); Result from executing a specific testcase for a specific run
            tc (Testcase object): The testcase corresponding to the result
            valgrind (ValgrindOutput object): The Valgrind output corresponding to the testcase result

        Returns: Nothing.
        """
        failed=[[tc_result, tc, valgrind]]
        print(table_format(
            '{id} | {valgrind} | {valgrind_rw} | {segfault} | {timeout} | {return} | {output} | {error_description}',
            cls.create_stats(failed),
            titles='auto'), file=sys.stdout)
        print(file=sys.stdout)

    @classmethod
    def create_stats(cls, results):
        """
        Function to generate a list of strings based. This list can then be used by table_format() to write a line.
        Parameters:
            results (List containing a TestcaseResult object, a Testcase object and a ValgrindOutput object) :
                Results from the execution of a specific submission on a specific testcase
        Returns:
            List of Strings
        """
        stats=list()
        for result, testcase, valgrind in results:
            line={'id': str(testcase.short_id)}
            line['valgrind']=str(valgrind.ok) if valgrind is not None else ""
            line['valgrind_rw']=str(valgrind.invalid_read_count+valgrind.invalid_write_count) if valgrind is not None else ""
            line['segfault']=str(result.segfault)
            line['timeout']=str(result.timeout)
            line['return']=str(result.return_code)
            line['output']=str(result.output_correct)
            line['error_description']=str(result.error_msg_quality)
            stats.append(line)
        return stats

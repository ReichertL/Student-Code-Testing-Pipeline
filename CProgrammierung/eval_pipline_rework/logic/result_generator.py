"""
    Module to implement needed functionality to generate all
    statistics and summaries.
"""
import csv
import datetime
import sys
import logging

from alchemy.students import Student
from alchemy.submissions import Submission
from alchemy.runs   import Run
from alchemy.testcase_results import Testcase_Result
from alchemy.testcases import Testcase

from util.colored_massages import red, yellow, green
from util.htable import table_format

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)

class ResultGenerator:
    """
    Class to implement needed functionality to generate all
    statistics and summaries.
    Might be extendet.
    """

    to_dump_list = []

    def __init__(self):
        self.csv_path = "moodle_result_dump.csv"
        self.csv_mailed_path = "moodle_success_mailed_dump.csv"
        self.abtestat_done_path = "abtestat_done_dump.csv"
        self.to_dump_list.append(["ID", "Name", "Punkte"])

    def generate_csv_dump(self,):
        """
        Generates all necessary csv-files
        which provides student information
        :return:nothing
        """

        passed_students = Student.get_students_passed()
        with open(self.csv_path, "w") as result_file:
            result_writer = csv.writer(result_file, delimiter=",")
            header = ["ID", "Name", "Punkte"]
            result_writer.writerow(header)
            for s in passed_students:
                    row = [s.matrikel_nr, s.name, s.grade]
                    result_writer.writerow(row)


        with open(self.abtestat_done_path, "w") as result_file:
            result_writer = csv.writer(result_file, delimiter=",")

            abtestat_done = Student.get_abtestat_done()
            if len(abtestat_done) > 0:
                header = ["Name", "Matrikelnr.", "Zeitstempel"]
                result_writer.writerow(header)
                for s in abtestat_done:
                    row = [s.name,
                           s.matrikel_nr,
                           s.abtestat_time\
                           .strftime("%H:%M:%S %d-%m-%Y")]
                    result_writer.writerow(row)

    @staticmethod
    def print_summary_stats_small():
        """
        prints summarized stats for all stundents that have at least
        one submission which is checked
        :param database_manager: the database manager
        that provides student information
        :return: nothing
        """
        all_students = Student.get_students_all()
        for student in all_students:
            sub_stud = Submission.get_all_for_name(student.name)
            if len(sub_stud) > 0:
                print(f"Stats for {student.name}")
            for submission, student in sub_stud:
                if submission.is_checked:
                    print(f"Submission from the {submission.submission_time}")
                    run=Run.get_last_for_submission(submission)
                    self.print_small_stats(run, sys.stdout)

    def add_line(self, student):
        """
        adds a line to the list of students
        that should be contained in the csv result dump
        :param student: the student entity
        :param points: the points he/she received
        :return: nothing
        """
        row = [student.matrikel_nr, student.name, student.grade]
        self.to_dump_list.append(row)

    def dump_list(self):
        """
        dumps a csv list for all students who have received a mail
        :return: nothing
        """
        if len(self.to_dump_list) > 1:
            with open(self.csv_mailed_path, "w") as result_file:
                result_writer = csv.writer(result_file, delimiter=",")
                for i in self.to_dump_list:
                    result_writer.writerow(i)

    def print_details(self, details):
        """
        prints detailed information for all student names in details
        :param database_manager: database manager to retrieve the students list
        :param details: a list of raw student names
        :return:
        """
        for name in details:
            student = Student.get_student_by_name(name)
            if student is None:
                print(f"No student with this name {name} found!")
                continue
            print(f"Printing details for {name}:")
            sub_stud = Submission.get_all_for_name(name)
            logging.debug(sub_stud)
            if len(sub_stud) > 1:
                print("More than one submission found. Please select!")
                for index, pair in zip(range(0,len(sub_stud)),sub_stud):
                    submission,student=pair
                    print(f"[{index + 1}]: {submission.submission_time}")

                answer_accepted = False
                answer = 0
                while not answer_accepted:
                    answer = sys.stdin.readline()[0]
                    try:
                        answer = int(answer) - 1
                        if len(sub_stud) > answer >= 0:
                            answer_accepted = True
                        else:
                            print(f"{answer + 1} is not in range of"
                                  f"[{1},{len(sub_stud)}],"
                                  f"please select again!")
                    except ValueError:
                        print(f"{answer} is not a number,"
                              f"please select again!")

                run=Run.get_last_for_submission(sub_stud[answer][0])
                self.print_stats(run,sys.stdout)


            elif len(sub_stud) == 1:
                run=Run.get_last_for_submission(sub_stud[0][0])
                self.print_stats(run,sys.stdout)

            else:
                print("No submissions for this student found!")
                

    @classmethod    
    # use like: f=sys.stdout
    def print_small_stats(cls, run, f):
        output = ''
        if run.compilation_return_code!=0:
            output = output + (red('Compilation failed. '))
            print(output)
            return

        output = output + (green('Compilation successful. '))
        
        failed_bad=len(Testcase_Result.get_failed_bad(run))
        failed_good=len(Testcase_Result.get_failed_good(run))

        if run.passed and run.manual_overwrite_passed:
            failed_bad=0
            failed_good=0
            print(f'This run was manually marked as passed (run.id={run.id})')
            
        failed_bad=len(Testcase_Result.get_failed_bad(run))
        all = len(Testcase.get_all_bad())
        if failed_bad > 0:
            output = output + (red(f'{failed_bad} / {all} bad tests failed. '))
        else:
            output = output + (green(f'0 / {all} bad tests failed. '))

        
        all = len(Testcase.get_all_good())
        if failed_good > 0:
            output = output + (red(f'{failed_good} / {all} good tests failed. '))
        else:
            output = output + (green(f'0 / {all} good tests failed. '))

        print(output, file=f)
        

    @classmethod
    # use like: f=sys.stdout
    def print_stats(cls,run, f):
        if run.compilation_return_code!=0:
            print(red('compilation failed; compiler errors follow:'), file=f)
            print(hline, file=f)
            print(run.compilation.commandline, file=f)
            print(run.compilation.output, file=f)
            print(hline, file=f)
            return
        if len(run.compiler_output) > 0:
            print(yellow('compilation procudes the following warnings:'), file=f)
            print(hline, file=f)
            print(run.command_line, file=f)
            print(run.compiler_output, file=f)
            print(hline, file=f)
        
        failed_bad=Testcase_Result.get_failed_bad(run)
        failed_good=Testcase_Result.get_failed_good(run)

        if run.passed and run.manual_overwrite_passed:
            failed_bad=[]
            failed_good=[]
            print(f'This run was manually marked as passed (run.id={run.id})')
    
        if len(failed_bad)==0 and run.compilation_return_code==0:
            print(green('All tests concerning malicious input passed.'), file=f)
        else:
            all = len(Testcase.get_all_bad())
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
            all = len(Testcase.get_all_good())
            print(red(f'{len(failed_good)} / {all} tests concerning good input failed.')
                  , file=f)
            print(file=f)
            failed_good.sort(key=lambda x: x[1].short_id)
            print(table_format(
                '{id} | {valgrind} | {valgrind_rw} | {segfault} | {timeout} | {return} | {output} | {error_description}',
               cls.create_stats(failed_good),
                titles='auto'), file=f)
            print(file=f)

    @classmethod
    def print_stats_testcase_result(cls,tc_result, tc, valgrind):
        failed=[[tc_result,tc,valgrind]]
        print(table_format(
                '{id} | {valgrind} | {valgrind_rw} | {segfault} | {timeout} | {return} | {output} | {error_description}',
               cls.create_stats(failed),
                titles='auto'), file=sys.stdout)
        print(file=sys.stdout)

    @classmethod
    def create_stats(cls,results):
        stats=list()       
        for result, testcase, valgrind in results:
            line={'id':str(testcase.short_id)}
            line['valgrind']=str(valgrind.ok) if valgrind!=None else ""
            line['valgrind_rw']= str(valgrind.invalid_read_count+valgrind.invalid_write_count) if valgrind!=None else ""
            line['segfault']=str(result.segfault)
            line['timeout']=str(result.timeout)
            line['return']=str(result.return_code)
            line['output']=str(result.output_correct)
            line['error_description']=str(result.error_msg_quality)
            stats.append(line)
        return stats

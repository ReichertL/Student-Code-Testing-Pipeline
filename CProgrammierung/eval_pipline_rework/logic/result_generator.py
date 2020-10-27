"""
    Module to implement needed functionality to generate all
    statistics and summaries.
"""
import csv
import datetime
import sys

from alchemy.students import Student
from alchemy.submissions import Submission
from alchemy.runs   import Run

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
    def print_short_stats():
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
                    run.print_small_stats(sys.stdout)

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
            if len(sub_stud) > 1:
                print("More than one submission found. Please select!")
                for index, submission, _ in zip(range(0,len(sub_stud)),sub_stud):
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

                run=Run.get_last_for_submission(sub_stud[0][answer])
                run.print_stats(sys.stdout)


            elif len(sub_stud) == 1:
                run=Run.get_last_for_submission(sub_stud[0][0])
                run.print_stats(sys.stdout)

            else:
                print("No submissions for this student found!")

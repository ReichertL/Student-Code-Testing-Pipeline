import csv
import datetime
import sys


class ResultGenerator:
    to_dump_list = []

    def __init__(self):
        self.csv_path = "moodle_result_dump.csv"
        self.csv_mailed_path = "moodle_success_mailed_dump.csv"
        self.abtestat_done_path = "abtestat_done_dump.csv"
        self.to_dump_list.append(["ID", "Name", "Punkte"])

    def generate_csv_dump(self, database_manager):
        students = database_manager.get_all_students()
        passed_students = [i for i in students if i.passed]
        with open(self.csv_path, "w") as result_file:
            result_writer = csv.writer(result_file, delimiter=",")
            header = ["ID", "Name", "Punkte"]
            result_writer.writerow(header)
            for i in passed_students:
                if not database_manager.is_student_done(i):
                    row = [i.moodle_id, i.name, 1]
                    result_writer.writerow(row)
                else:
                    row = [i.moodle_id, i.name, 2]
                    result_writer.writerow(row)

        with open(self.abtestat_done_path, "w") as result_file:
            result_writer = csv.writer(result_file, delimiter=",")

            abtestat_done = database_manager.get_testat_information()
            if len(abtestat_done) > 0:
                header = ["ID", "Name", "Zeitstempel"]
                result_writer.writerow(header)
                for i in abtestat_done:
                    row = [database_manager
                               .get_student_by_key(i[0]).name,
                           i[1],
                           datetime
                               .datetime
                               .fromisoformat(i[2])
                               .strftime("%H:%M:%S %d-%m-%Y")]
                    result_writer.writerow(row)

    def print_short_stats(self, database_manager):
        student_log = database_manager.get_all_students()
        for student in student_log:
            submissions = student.get_all_submissions(database_manager)
            if len(submissions) > 0:
                print(f"Stats for {student.name}")
            for submission in submissions:
                if submission.is_checked:
                    submission.print_small_stats()

    def add_line(self, student, points):
        row = [student.moodle_id, student.name, points]
        self.to_dump_list.append(row)

    def dump_list(self):
        if len(self.to_dump_list) > 1:
            with open(self.csv_mailed_path, "w") as result_file:
                result_writer = csv.writer(result_file, delimiter=",")
                for i in self.to_dump_list:
                    result_writer.writerow(i)

    def print_details(self, database_manager, details):
        for raw_student in details:
            student = database_manager.get_student_by_name(raw_student)
            if student is None:
                print(f"No student with this name {raw_student} found!")
                continue
            print(f"Printing details for {raw_student}:")
            submissions = database_manager.get_submissions_for_student(student)
            if len(submissions) > 1:
                print(f"More than one submission found. Please select!")
                for index, submission in zip(range(0, len(submissions)), submissions):
                    print(f"[{index + 1}]: {submission.timestamp}")

                answer_accepted = False
                answer = 0
                while not answer_accepted:
                    answer = sys.stdin.readline()[0]
                    try:
                        answer = int(answer) - 1
                        if len(submissions) > answer >= 0:
                            answer_accepted = True
                        else:
                            print(f"{answer + 1} is not in range of [{1},{len(submissions)}], please select again!")
                    except ValueError:
                        print(f"{answer} is not a number, please select again!")

                submissions[answer].print_stats()

            elif len(submissions) == 1:
                submissions[0].print_stats()

            else:
                print("No submissions for this student found!")

import csv


class ResultGenerator:
    def __init__(self):
        self.csv_path = "moodle_result_dump.csv"

    def generate_csv_dump(self, database_manager):
        students = database_manager.get_all_students()
        passed_students = [i for i in students if i.passed]
        with open(self.csv_path, "w") as result_file:
            result_writer = csv.writer(result_file, delimiter=",")
            header = ["ID", "Name", "Punkte"]
            result_writer.writerow(header)
            for i in passed_students:
                row = [i.moodle_id, i.name, 1]
                result_writer.writerow(row)

    def print_short_stats(self, database_manager):
        studentlog = database_manager.get_all_students()
        for student in studentlog:
            submissions = student.get_all_submissions(database_manager)
            if len(submissions) > 0:
                print(f"Stats for {student.name}")
            for submission in submissions:
                if submission.is_checked:
                    submission.print_small_stats()

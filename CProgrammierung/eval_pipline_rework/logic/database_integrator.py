import os
import sys
from pathlib import Path

from models.student import Student
from models.submission import Submission
from util.config_reader import ConfigReader


class DatabaseIntegrator:
    configuration: str

    def __init__(self):
        file_name = sys.argv[0]
        file_name = file_name.replace("__main__.py", "").replace(".", "")
        config_path = Path(file_name + "resources/config_database_integrator.config").resolve()
        configuration = ConfigReader().read_file(config_path)
        self.configuration = configuration

    def integrate_submission_dir(self, database_manager):
        base_dir = self.configuration["SUBMISSION_BASE_DIR"]
        for root, _, files in os.walk(
                base_dir
                ,
                topdown=False):
            student_details = root.replace(os.path.join(base_dir, ), "").replace(os.path.sep, "").replace(
                "_assignsubmission_file_", "")
            student_name = student_details[0:student_details.find("_")]
            student_moodle_id = student_details[student_details.find("_") + 1:]

            if len(student_name) > 0 and len(student_moodle_id) > 0:
                new_student = Student(student_name, student_moodle_id, persistence_manager=database_manager)
            for file in files:
                new_submission = Submission()
                new_submission.path = root + os.path.sep + file
                database_manager.insert_submission(new_student, new_submission)

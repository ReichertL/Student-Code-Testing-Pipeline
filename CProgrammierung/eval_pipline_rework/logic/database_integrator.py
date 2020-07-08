import datetime
import os
import re
import shutil

from models.submission import Submission
from util.absolute_path_resolver import resolve_absolute_path
from util.config_reader import ConfigReader


class DatabaseIntegrator:
    configuration: str

    def __init__(self):
        config_path = resolve_absolute_path("/resources/config_database_integrator.config")
        configuration = ConfigReader().read_file(config_path)
        self.configuration = configuration

    def integrate_submission_dir(self, database_manager):
        base_dir = resolve_absolute_path(self.configuration["SUBMISSION_BASE_DIR"])
        for root, _, files in os.walk(
                base_dir
                ,
                topdown=False):
            student_details = root.replace(os.path.join(base_dir, ), "").replace(os.path.sep, "").replace(
                "_assignsubmission_file_", "")
            student_name = student_details[0:student_details.find("_")]
            student_moodle_id = student_details[student_details.find("_") + 1:]
            if len(student_name) > 0 and len(student_moodle_id) > 0:
                new_student = database_manager.get_student_by_name(student_name)
            for file in files:
                filename = file
                if not file.startswith("loesung_202"):
                    timestamp_extension = datetime.datetime.fromtimestamp(
                        int(os.path.getmtime(root + os.path.sep + file))).__str__()
                    regex_timestamp = re.sub("-|:|\s", "_", timestamp_extension)
                    filename = f"loesung_{regex_timestamp}.c"
                    new_file = os.path.join(root, filename)
                    old_file = os.path.join(root, file)
                    shutil.move(old_file, new_file)

                new_submission = Submission()
                new_submission.path = root + os.path.sep + filename
                new_submission.mtime = int(os.path.getmtime(new_submission.path))
                database_manager.insert_submission(new_student, new_submission)

"""
Modularity to integrate a directory into the database
"""

import datetime
import os
import re
import shutil
import logging

#from models.submission import Submission
from database.submissions import Submission
from database.students import Student
from database.database_manager import DatabaseManager 

from util.absolute_path_resolver import resolve_absolute_path
from util.config_reader import ConfigReader


FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)

class DatabaseIntegrator:
    """
    Modularity to integrate a directory into the database
    """
    configuration: str

    def __init__(self):
        config_path = resolve_absolute_path(
            "/resources/config_database_integrator.config")
        configuration = ConfigReader().read_file(config_path)
        self.configuration = configuration

    def __str__(self):
        return "DatabaseIntegrator"

    def integrate_submission_dir(self):
        """
        given a submission directory
        this function integrates all
        submissions in it in the format
        studentname_
        submissionid_
        _assignsubmission_file_
        into the database
        :param database_manager: the database manager where the
        submission shall be integrated
        :return: nothing
        """
        base_dir = resolve_absolute_path(
            self.configuration["SUBMISSION_BASE_DIR"])
        for root, _, files in os.walk(base_dir,topdown=False):
            student_details = root \
                .replace(os.path.join(base_dir, ), "") \
                .replace(os.path.sep, "") \
                .replace("_assignsubmission_file_", "")
            student_name = student_details[0:student_details.find("_")]
            wired_id = student_details[student_details.find("_") + 1:]
            if len(student_name) > 0 and len(wired_id) > 0:
                student = Student.get_student_by_name(student_name)
            for file in files:
                if file.__str__().find(".swp") > 0:
                    continue
                filename = file

                if not file.startswith("loesung_202"):
                    timestamp_extension = datetime.datetime.fromtimestamp(
                        int(os.path.getmtime(root + os.path.sep + file))) \
                        .__str__()
                    regex_timestamp = re.sub("-|:|\s", "_",
                                             timestamp_extension)
                    #now=datetime.datetime.now()
                    #ts_string=now.strftime("%Y-%m-%d_%H-%M-%S")
                    filename = f"loesung_{regex_timestamp}.c"
                    new_file = os.path.join(root, filename)
                    old_file = os.path.join(root, file)
                    shutil.move(old_file, new_file)
                path=root + os.path.sep + filename
                time_from_filename=filename[8:-2]
                ts=datetime.datetime.strptime(time_from_filename,"%Y_%m_%d_%H_%M_%S")
                Submission.insert_submission(student, path, ts)
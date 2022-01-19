"""
Modularity to integrate  submissions into the database.
When downloading submissions to  an exercise with moodle,
a zip is created with the most recent submission of each student.
To integrate new submissions into the database, the zip is unpacked and checked if a
corresponding file has already been handed in by the student.
"""

from datetime import datetime
import os
import re
import shutil
import logging
from database.submissions import Submission
from database.students import Student
from util.absolute_path_resolver import resolve_absolute_path
from util.config_reader import ConfigReader

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


class DatabaseIntegrator:
    """
    Module to integrate new submissions into the database.
    """
    configuration: str

    def __init__(self):
        """
        Initialises the DatabaseIntegrator using a config file.
        """
        config_path=resolve_absolute_path(
            "/resources/config_database_integrator.config")
        configuration=ConfigReader().read_file(config_path)
        self.configuration=configuration

    def __str__(self):
        return "DatabaseIntegrator"

    def integrate_submission_dir(self):
        """
        This function integrates a directory containing student submissions into the database.

        When downloading submissions to  an exercise with moodle,
        a zip is created with the most recent submission of each student.
        The unpacked zip is located in a folder set by the configuration file for the database integrator.
        In this directory each student who has submitted has his own subdirectory containing a file.
        Only a single file is accepted which starts with the string loesung_2022.c,
         where 2022 represents the current year.
        The submission is integrated into the database if it does not already exist.

            "Given a submission directory
            this function integrates all
            submissions in it in the format
            studentname_
            submissionid_
            _assignsubmission_file_
            into the database"
        Parameters: None
        Returns: Nothing
        """
        base_dir=resolve_absolute_path(
            self.configuration["SUBMISSION_BASE_DIR"])
        for root, _, files in os.walk(base_dir, topdown=False):
            student_details=root \
                .replace(os.path.join(base_dir, ), "") \
                .replace(os.path.sep, "") \
                .replace("_assignsubmission_file_", "")
            student_name=student_details[0:student_details.find("_")]
            moodle_id=student_details[student_details.find("_")+1:] 
            
            if len(student_name)>0 and len(moodle_id)>0:
                student=Student.get_student_by_name(student_name)
            for file in files:
                if file.__str__().find(".swp")>0:
                    continue
                filename=file
                
                path=root+os.path.sep+filename
                time_from_filename=filename[8:-2]
                ts=datetime.strptime(time_from_filename, "%Y_%m_%d_%H_%M_%S")
                Submission.insert_submission(student, path, ts)

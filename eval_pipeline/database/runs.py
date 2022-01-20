"""
SQL Alchemy classed used to create table "Run". Also contains functions that query the database for table "Run".
A run contains the information about the execution of a specific submission.
The ID of a run can be used to find results for individual testcases in different tables.
One submission can have multiple runs, as commandline parameters between runs can differ.
"""

import logging
from functools import cmp_to_key
from sqlalchemy import *
from database.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression
import database.database_manager as dbm
from database.testcase_results import TestcaseResult
from database.valgrind_outputs import ValgrindOutput
from database.testcases import Testcase
import database.submissions as sub
import database.students as stud

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


class Run(Base):
    __tablename__='Run'
    # Columns of table "Run"
    id=Column(Integer, primary_key=True)
    submission_id=Column(Integer, ForeignKey("Submission.id"), nullable=False)
    careless_flag=Column(Boolean, default=False, server_default=expression.false())
    command_line=Column(String, nullable=False)
    compilation_return_code=Column(Integer, nullable=False)
    compiler_output=Column(String, nullable=False)

    execution_time=Column(DateTime)
    passed=Column(Boolean, default=False, server_default=expression.false())
    manual_overwrite_passed=Column(Boolean)

    # foreign key relationship to table TestcaseResult
    testcase_results=relationship("TestcaseResult", backref="Run.id")

    def __init__(self, submission_id, command_line, careless_flag, compilation_return_code, compiler_output):
        """
        Create new row for table "Run".
        Parameters:
            submission_id (int): ID of the submission corresponding to this run.
            command_line (string): Command used to compile submission.
            careless_flag (bool): If the careless flag was set to true.  This means warnings are ignored.
            compilation_return_code (int): Return code from compiling the submission
            compiler_output (string): Output of compiler when finished. If there are warnings and errors, they will be contained in this string.
        """
        self.submission_id=submission_id
        self.command_line=command_line
        self.careless_flag=careless_flag
        self.compilation_return_code=compilation_return_code
        self.compiler_output=compiler_output

    def __repr__(self):
        return ("(Run: "+str(self.id)+","+
                str(self.submission_id)+","+
                str(self.command_line)+","+
                str(self.compilation_return_code)+","+
                str(self.compiler_output)+")")

    @classmethod
    def is_passed(cls, r):
        """
        Check for run r if it is  passed.
        Parameters:
            r (Run object)
        Returns:
            Boolean
        """
        count=dbm.session.query(TestcaseResult) \
            .join(ValgrindOutput, isouter=True) \
            .filter(TestcaseResult.run_id==r.id) \
            .filter(or_(ValgrindOutput.ok==False, TestcaseResult.output_correct==False)).count()
        if count==0 and r.compilation_return_code==0:
            return True
        return False

    @classmethod
    def insert_run(cls, run):
        """
        Inserts a run into table "Run" if it does not already exist. Checks submission_id, command_line and careless_flag.
        Parameters:
            run (Run object)
        Returns:
            run if it did not exist or the existing run from the database.
        """

        exists=dbm.session.query(Run)\
            .filter(Run.submission_id==run.submission_id, Run.command_line==run.command_line, Run.careless_flag==run.careless_flag).first()
        if exists is None:
            dbm.session.add(run)
            dbm.session.commit()
            return run
        return exists

    @classmethod
    def get_last_for_submission(cls, submission):
        """
        Gets last run for a specific submission which passed. 
        Parameters:
            submission (Submission object)
        Returns:
            run or None        
        """
        run=dbm.session.query(Run)\
            .filter(Run.submission_id==submission.id, Run.passed==True)\
            .order_by(Run.execution_time.desc()).first()
        if run is None:
            run=dbm.session.query(Run).filter(Run.submission_id==submission.id).order_by(
                Run.execution_time.desc()).first()
        return run

    @staticmethod
    def comperator_performance(run1, run2):
        """
        Compares performance of two runs using the average runtime (over all testcases).
         WARNING: This function probably has issues.
        Parameters:
            run1 (Run object)
            run2 (Run object)
        returns
            Difference of average runtimes for the two runs.
        """
        t1=TestcaseResult.get_avg_runtime_performance(run1)  # TODO requires keylist
        t2=TestcaseResult.get_avg_runtime_performance(run2)  # TODO requires keylist
        return t2-t1

    @classmethod
    def get_fastest_run_for_student(self, name, keylist):
        """
        Gets the fastest run for a student.
        Parameters:
            name (string): name of the student as in database.
            keylist (list of ints): List of testcase IDs to use for calculating the average runtime
            
        Returns:
            None if no runs are found or if there are no runs which were not manually set to "Passed"
            else, the fastest_run (Run object) the fastest run for this student 
                
        """
        logging.debug(name)
        results=dbm.session.query(Run, sub.Submission) \
            .join(sub.Submission).join(stud.Student) \
            .filter(Run.passed==True) \
            .filter(sub.Submission.is_fast==True, stud.Student.name==name).all()
        performance=list()
        for run, submission in results:
            time=TestcaseResult.get_avg_runtime_performance(run, keylist)
            space=TestcaseResult.get_avg_space_performance(run, keylist)
            if run.manual_overwrite_passed!=True:
                performance.append([run, submission, time, space])
        if len(performance)>0:
            fastest_run=performance[0]
            fastest_time=TestcaseResult.get_avg_runtime_performance(run, keylist)
            for r in performance:
                r_time=TestcaseResult.get_avg_runtime_performance(run, keylist)
                if r_time<fastest_time:
                    fastest_run=r
                    fastest_time=r_time
            return fastest_run
        return None

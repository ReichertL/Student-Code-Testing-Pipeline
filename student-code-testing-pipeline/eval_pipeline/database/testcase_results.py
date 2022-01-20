"""
SQL Alchemy classed used to create table "TestcaseResult".
Also contains functions that query the database for table "TestcaseResult".
TestcaseResults contain information regarding the execution of a specific testcase for a specific submission/run.
For TestcaseResults where the Testcase requires an analysis with Valgrind, a corresponding ValgrindOutput is created.
"""

import logging
from sqlalchemy import *
from database.base import Base
from sqlalchemy.orm import relationship
from database.testcases import Testcase
from database.valgrind_outputs import ValgrindOutput
import database.database_manager as dbm

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


class TestcaseResult(Base):
    __tablename__='TestcaseResult'
    # Columns for the table "TestcaseResult"
    id=Column(Integer, primary_key=True)
    run_id=Column(Integer, ForeignKey("Run.id"), nullable=False)
    testcase_id=Column(Integer, ForeignKey("Testcase.id"), nullable=False)

    output_correct=Column(Boolean)  # relevant to all testcases
    return_code=Column(Integer)
    signal=Column(Integer)
    segfault=Column(Boolean)
    timeout=Column(Boolean)
    cpu_time=Column(Float)
    tictoc=Column(Float)
    mrss=Column(Integer)

    rlimit_data=Column(Integer)
    rlimit_stack=Column(Integer)
    rlimit_cpu=Column(Integer)
    used_valgrind_data=Column(Integer)
    used_valgrind_stack=Column(Integer)
    used_valgrind_cpu=Column(Integer)
    num_executions=Column(Integer)

    # only relevant for testcases that test if the submission fails successfully
    error_msg_quality=Column(Integer)
    error_line=Column(String)

    # foreign key relationship to table TestcaseResult
    valgrind_results=relationship("ValgrindOutput", uselist=False, backref="TestcaseResult.id")

    def __init__(self, run_id, testcase_id):
        self.run_id=run_id
        self.testcase_id=testcase_id

    def __repr__(self):
        return ("(TestcaseResult: "+str(self.id)+","+
                str(self.run_id)+","+
                str(self.testcase_id)+","+
                str(self.output_correct)+","+
                str(self.return_code)+","+
                str(self.signal)+","+
                str(self.timeout)+")")

    def returncode_correct(self, testcase=None):
        """
        Checks if the return code for the testcase means if the testcase is passed or not. 
        "BAD" testcases are correct  if the students code returned with an Error code.
        "GOOD" testcases are correct if the students code did not return an Error code.
        "BAD_OR_OUTPUT" are correct if the return code was 0 and the output was correct or if it was not zero and an Error was returned.
        
        Parameters:
            testcase () : Optional. Information can also be optained if testcase_id is set.
        
        """
        if testcase is None:
            testcase=Testcase.get_by_id(self.testcase_id)

        if testcase.type=="BAD":
            if self.return_code>0:
                return True
            else:
                return False
        if testcase.type=="GOOD" or testcase.type=="PERFORMANCE":
            if self.return_code==0:
                return True
            else:
                return False
        if testcase.type=="BAD_OR_OUTPUT":  # TODO not tested
            if self.return_code==0 and self.output_correct==True: return True
            if self.return_code>0 and self.segfault!=True and self.error_msg_quality!="":
                return True
            else:
                return False
        return True

    @classmethod
    def create_or_get(cls, r_id, tc_id):
        """
        Create a new testcase result,  if it already exists get the corresponding TestcaseResult object.
        Parameters:
            r_id (int): ID of Run
            tc_id (int): ID of Testcase
        
        Returns:
            TestcaseResult object
        
        """
        testcase_result=dbm.session.query(TestcaseResult).filter_by(run_id=r_id, testcase_id=tc_id).first()
        if testcase_result is None:
            new_testcase_result=TestcaseResult(r_id, tc_id)
            dbm.session.add(new_testcase_result)
            dbm.session.commit()
            return new_testcase_result
        return testcase_result

    @classmethod
    def get_testcase_result_by_run_and_testcase(cls, run_id, testcase_id=None, testcase_name=None):
        """
        Returns a testcase result given a run_id and either a testcase ID or the name of the testcase.
        Parameters:
            run_id (int): ID of the run
            testcase_id (int): ID of the testcase. Optional.
            testcase_name (string): Name of the testcase. 
        Returns:
            TestcaseResult object
        
        """
        if testcase_id is None and testcase_name is None:
            logging.error(
                "Provide either testcase_id or testcase_name when calling get_testcase_result_by_run_and_testcase().")
            exit(1)
        result=None
        if testcase_id is not None:
            result=dbm.session.query(TestcaseResult).join(Testcase) \
                .filter(TestcaseResult.run_id==run_id, Testcase.id==testcase_id).first()
        elif testcase_name is not None:
            result=dbm.session.query(TestcaseResult).join(Testcase) \
                .filter(TestcaseResult.run_id==run_id, Testcase.short_id==testcase_name).first()

        return result

    @classmethod
    def get_failed_good(cls, run):
        """
        Get all testcase results for a certain run which have failed and which have the type "GOOD"
        (so those where the students code should return the correct result).
        It can be failed either because the output was false or because the Valgrind output was not ok.
        This is the case if there has been a memory leak.
        
        Parameters:
            run (Run object) 
            
        Returns:
            List of tuples each containing a TestcaseResult , a Testcase and a ValgrindOutput object.
        
        """
        failed_testcases=dbm.session.query(TestcaseResult, Testcase, ValgrindOutput) \
            .join(Testcase, Testcase.id==TestcaseResult.testcase_id) \
            .join(ValgrindOutput, ValgrindOutput.testcase_result_id==TestcaseResult.id, isouter=True) \
            .filter(TestcaseResult.run_id==run.id, Testcase.type=="GOOD") \
            .filter(or_(TestcaseResult.output_correct==False, ValgrindOutput.ok==False)) \
            .all()
        return failed_testcases

    @classmethod
    def get_failed_bad(cls, run):
        """
        Get all testcase results for a certain run which have failed and which have the type "BAD"
        (so those where the students code should fail gracefully).
        It can be failed either because the output was false (e.g. no error message)
        or because the Valgrind output was not ok (e.g. there was a memory leak).
        
        Parameters:
            run (Run object) 
            
        Returns:
            List of tuples each containing a TestcaseResult , a Testcase and a ValgrindOutput object.
        
        """
        failed_testcases=dbm.session.query(TestcaseResult, Testcase, ValgrindOutput) \
            .join(Testcase, Testcase.id==TestcaseResult.testcase_id) \
            .join(ValgrindOutput, ValgrindOutput.testcase_result_id==TestcaseResult.id, isouter=True) \
            .filter(TestcaseResult.run_id==run.id) \
            .filter(or_(Testcase.type=="BAD", Testcase.type=="BAD_OR_OUTPUT")) \
            .filter(or_(ValgrindOutput.ok==False, TestcaseResult.output_correct==False)) \
            .all()
        return failed_testcases

    @classmethod
    def get_failed_output_good(cls, run):
        """
        Get all testcase results for a certain run which have failed and which have the type "GOOD"
        (so those where the students code should return the correct result).
        Valgrind is ignored here.
        
        Parameters:
            run (Run object) 
            
        Returns:
            List of tuples each containing a TestcaseResult and a Testcase  object.
        
        """
        failed_testcases=dbm.session.query(TestcaseResult, Testcase) \
            .join(Testcase, Testcase.id==TestcaseResult.testcase_id) \
            .filter(TestcaseResult.run_id==run.id, Testcase.type=="GOOD") \
            .filter(TestcaseResult.output_correct==False) \
            .all()
        return failed_testcases

    @classmethod
    def get_failed_output_bad(cls, run):
        """
        Get all testcase results for a certain run which have failed and which have the type "BAD"
        (so those where the students code should fail gracefully).
        Valgrind is ignored here.
        
        Parameters:
            run (Run object) 
            
        Returns:
            List of tuples each containing a TestcaseResult and a Testcase  object.
        
        """
        failed_testcases=dbm.session.query(TestcaseResult, Testcase) \
            .join(Testcase, Testcase.id==TestcaseResult.testcase_id) \
            .filter(TestcaseResult.run_id==run.id) \
            .filter(Testcase.type=="BAD") \
            .filter(TestcaseResult.output_correct==False) \
            .all()
        return failed_testcases

    @classmethod
    def get_failed_output_bad_or_output(cls, run):
        """
        Get all testcase results for a certain run which have failed and which have the type "BAD_OR_OUTPUT"
        (so those where the students code should fail gracefully or return the correct answer).
        Valgrind is ignored here.
        
        Parameters:
            run (Run object) 
            
        Returns:
            List of tuples each containing a TestcaseResult and a Testcase  object.
        
        """

        failed_testcases=dbm.session.query(TestcaseResult, Testcase) \
            .join(Testcase, Testcase.id==TestcaseResult.testcase_id) \
            .filter(TestcaseResult.run_id==run.id) \
            .filter(Testcase.type=="BAD_OR_OUTPUT") \
            .filter(TestcaseResult.output_correct==False) \
            .all()
        return failed_testcases

    @classmethod
    def get_bad_for_run(cls, run):
        """
        Get all testcases results for a certain run which have the type "BAD"
        (so those where the students code should fail gracefully).
        
        Parameters:
            run (Run object) 
            
        Returns:
            List of TestcaseResult  object.
        
        """
        results=dbm.session.query(TestcaseResult)\
            .join(Testcase)\
            .filter(Testcase.type=="BAD", TestcaseResult.run_id==run.id).all()
        return results

    @classmethod
    def get_good_for_run(cls, run):
        """
        Get all testcases results for a certain run which have the type "GOOD"
        (so those where the students code should return the correct result).
        
        Parameters:
            run (Run object) 
            
        Returns:
            List of TestcaseResult  object.
        
        """
        results=dbm.session.query(TestcaseResult)\
            .join(Testcase)\
            .filter(Testcase.type=="GOOD", TestcaseResult.run_id==run.id).all()
        return results

    @classmethod
    def get_avg_runtime(cls, r):
        """
        Getting the average runtime for a certain run by calculating the mean over all testcase results of this run
        which belong to a "GOOD" testcases.
        Uses the tictoc field of each testcase result.
        Parameters:
            r (Run object)
            
        Returns:
            Avarage as Float
        """
        avg=dbm.session.query(func.avg(TestcaseResult.tictoc))\
            .join(Testcase)\
            .filter(TestcaseResult.run_id==r.id, Testcase.type=="GOOD")\
            .scalar()
        return avg

    @classmethod
    def get_avg_space(cls, r):
        """
        Getting the average space consumption for a certain run by calculating the mean over all testcase results of
        this run which belong to a "GOOD" testcases.
        Uses the mrss field of each testcase result.
        Parameters:
            r (Run object)
            
        Returns:
            Average as Float
        """
        avg=dbm.session.query(func.avg(TestcaseResult.mrss))\
            .join(Testcase)\
            .filter(TestcaseResult.run_id==r.id, Testcase.type=="GOOD").scalar()
        return avg

    @classmethod
    def get_avg_runtime_performance(cls, r, keylist):
        """
        Getting the average runtime for a certain run.
        It calculates the mean over all testcases which are passed in keylist.
        Uses the tictoc field of each testcase result.
        Parameters:
            r (Run object)
            keylist (list of ints): List containing the IDs of testcases that are selected for the performance evaluation 
            
        Returns:
            Average as Float
        """
        avg=dbm.session.query(func.avg(TestcaseResult.tictoc))\
            .join(Testcase)\
            .filter(TestcaseResult.run_id==r.id)\
            .filter(Testcase.short_id.in_(keylist))\
            .scalar()
        return avg

    @classmethod
    def get_avg_space_performance(cls, r, keylist):
        """
        Getting the average space consumption for a certain run.
        It calculates the mean over all testcases which are passed in keylist.
        Uses the mrss field of each testcase result.
        Parameters:
            r (Run object)
            keylist (list of ints): List containing the IDs of testcases that are selected for the performance evaluation 
            
        Returns:
            Average as Float
        """

        avg=dbm.session.query(func.avg(TestcaseResult.mrss))\
            .join(Testcase)\
            .filter(TestcaseResult.run_id==r.id)\
            .filter(Testcase.short_id.in_(keylist))\
            .scalar()
        return avg

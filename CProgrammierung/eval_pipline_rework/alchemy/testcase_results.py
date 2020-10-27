import logging

from sqlalchemy import *
from alchemy.base import Base
from sqlalchemy.orm import relationship

from alchemy.testcases import Testcase
from alchemy.valgrind_outputs import Valgrind_Output
import alchemy.database_manager as dbm

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)


class Testcase_Result(Base):
    __tablename__ = 'Testcase_Result'
   
    id = Column(Integer, primary_key =  True)
    run_id=Column(Integer,  ForeignKey("Run.id"),nullable=False)
    testcase_id=Column(Integer,  ForeignKey("Testcase.id"),nullable=False)
    
    output_correct=Column(Boolean) #relevant to all testcases
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

    #relevant for bad testcases
    error_msg_quality=Column(Integer)
    error_line=Column(String)



    valgrind_results = relationship("Valgrind_Output", uselist=False, backref="Testcase_Result.id")
   
    def __init__(self, run_id, testcase_id):   
        self.run_id = run_id
        self.testcase_id=testcase_id

    def __repr__(self):
        return ("(Testcase_Result: " + str(self.id) + "," + \
                                str(self.run_id) + "," + \
                                str(self.testcase_id) + "," + \
                                str(self.output_correct) + "," + \
                                str(self.return_code) + "," + \
                                str(self.signal) + "," + \
                                str(self.timeout)  +")")
    
    
    def returncode_correct(self, testcase=None):
        if testcase==None:
            testcase=Testcase.get_by_ID(self.testcase_id)
        
        if testcase.type=="BAD":
            if self.return_code>0:return True
            else: return False
        if testcase.type=="GOOD" or testcase.type=="PERFORMANCE":
            if self.return_code==0: return True
            else: return False
        if testcase.type=="BAD_OR_OUTPUT":
            if self.return_code==0 and self.output_correct==True: return True
            if self.return_code>0 and self.segfault!=True and error_msg_quality!="": return True
            else: return False
        return True
    
    
    @classmethod
    def create_or_update(cls, r_id,tc_id):
        testcase_result=dbm.session.query(Testcase_Result).filter_by(run_id=r_id, testcase_id=tc_id).first()
        if testcase_result==None:
            new_testcase_result=Testcase_Result(r_id,tc_id)
            dbm.session.add(new_testcase_result)
            dbm.session.commit()
            return new_testcase_result
        return testcase_result
    
    @classmethod    
    def get_failed_good(cls,run ): 
        failed_testcases=dbm.session.query(Testcase_Result,Testcase,Valgrind_Output)\
                .join(Testcase, Testcase.id==Testcase_Result.testcase_id)\
                .join(Valgrind_Output,Valgrind_Output.testcase_result_id==Testcase_Result.id, isouter=True)\
                .filter(Testcase_Result.run_id==run.id, Testcase.type=="GOOD")\
                .filter(or_(Testcase_Result.output_correct==False,Valgrind_Output.ok==False))\
                .all()
        return failed_testcases
    
    @classmethod        
    def get_failed_bad(cls,run): 
        failed_testcases=dbm.session.query(Testcase_Result,Testcase,Valgrind_Output)\
                .join(Testcase, Testcase.id==Testcase_Result.testcase_id)\
                .join(Valgrind_Output,Valgrind_Output.testcase_result_id==Testcase_Result.id, isouter=True)\
                .filter(Testcase_Result.run_id==run.id)\
                .filter(or_(Testcase.type=="BAD",Testcase.type=="BAD_OR_OUTPUT"))\
                .filter(or_(Valgrind_Output.ok==False, Testcase_Result.output_correct==False))\
                .all()
        return failed_testcases
 
    @classmethod    
    def get_failed_output_good(cls,run ): 
        failed_testcases=dbm.session.query(Testcase_Result,Testcase)\
                .join(Testcase, Testcase.id==Testcase_Result.testcase_id)\
                .filter(Testcase_Result.run_id==run.id, Testcase.type=="GOOD")\
                .filter(Testcase_Result.output_correct==False)\
                .all()
        return failed_testcases
    
    @classmethod        
    def get_failed_output_bad(cls,run): 
        failed_testcases=dbm.session.query(Testcase_Result,Testcase)\
                .join(Testcase, Testcase.id==Testcase_Result.testcase_id)\
                .filter(Testcase_Result.run_id==run.id)\
                .filter(Testcase.type=="BAD")\
                .filter(Testcase_Result.output_correct==False)\
                .all()
        return failed_testcases

    @classmethod        
    def get_failed_output_bad_or_output(cls,run): 
        failed_testcases=dbm.session.query(Testcase_Result,Testcase)\
                .join(Testcase, Testcase.id==Testcase_Result.testcase_id)\
                .filter(Testcase_Result.run_id==run.id)\
                .filter(Testcase.type=="BAD_OR_OUTPUT")\
                .filter(Testcase_Result.output_correct==False)\
                .all()
        return failed_testcases
 
 
    @classmethod
    def get_bad_for_run(cls, run):
        results=dbm.session.query(Testcase_Results).join(Testcases).filter(Testcases.type=="BAD", Testcase_Result.run_id==run.id).all()
        return results

    @classmethod
    def get_good_for_run(cls, run):
        results=dbm.session.query(Testcase_Results).join(Testcases).filter(Testcases.type=="GOOD", Testcase_Result.run_id==run.id).all()
        return results
    
    @classmethod
    def get_avg_runtime(cls,r):
        avg=dbm.session.query(func.avg(Testcase_Result.tictoc)).filter_by(run_id=r.id).scalar()
        return avg

    @classmethod
    def get_avg_runtime_performance(cls,r , testcase_type):
        avg=dbm.session.query(func.avg(Testcase_Result.tictoc)).join(Testcase).filter(Testcase_Result.run_id==r.id, Testcase.type=="PERFORMANCE" ).scalar()
        return avg
 

        

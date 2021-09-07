import logging
from functools import cmp_to_key

from sqlalchemy import *
from database.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression


import database.database_manager as dbm
from database.testcase_results import Testcase_Result
from database.valgrind_outputs import Valgrind_Output
from database.testcases import Testcase
import database.submissions as sub
import database.students as stud



FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)

class Run(Base):
    __tablename__ = 'Run'
   
    id = Column(Integer, primary_key =  True)
    submission_id=Column(Integer,  ForeignKey("Submission.id"),nullable=False)
    careless_flag = Column(Boolean, default=False,server_default=expression.false())
    command_line=Column(String, nullable=False)
    compilation_return_code = Column(Integer, nullable=False)
    compiler_output=Column(String, nullable=False)
   
    execution_time = Column(DateTime)
    passed = Column(Boolean, default=False,server_default=expression.false())
    manual_overwrite_passed= Column(Boolean)

    testcase_results = relationship("Testcase_Result", backref="Run.id")
   
    def __init__(self, submission_id, command_line, careless_flag, compilation_return_code,compiler_output):   
        self.submission_id = submission_id
        self.command_line=command_line
        self.careless_flag=careless_flag
        self.compilation_return_code=compilation_return_code
        self.compiler_output=compiler_output


    def __repr__(self):
        return ("(Run: " + str(self.id) + "," + \
                                str(self.submission_id) + "," + \
                                str(self.command_line) + "," + \
                                str(self.compilation_return_code) + "," + \
                                str(self.compiler_output)  +")")




  
   
    @classmethod
    def is_passed(cls,r):
        count=dbm.session.query(Testcase_Result)\
            .join(Valgrind_Output, isouter=True)\
            .filter(Testcase_Result.run_id==r.id)\
            .filter(or_(Valgrind_Output.ok==False, Testcase_Result.output_correct==False)).count()
        if count==0 and r.compilation_return_code==0:
            return True
        return False

    @classmethod
    def insert_run(cls,run):
        exists=dbm.session.query(Run).filter(Run.submission_id==run.submission_id, Run.command_line==run.command_line, Run.careless_flag==run.careless_flag).first()
        if exists==None:
            dbm.session.add(run)
            dbm.session.commit()
            return run
        return exists   
    
    @classmethod
    def get_last_for_submission(cls,submission):
        run=dbm.session.query(Run).filter(Run.submission_id==submission.id, Run.passed==True).order_by(Run.execution_time.desc()).first()
        if run==None:
            run=dbm.session.query(Run).filter(Run.submission_id==submission.id).order_by(Run.execution_time.desc()).first()
        return run

    @staticmethod
    def comperator_performance(run1,run2):
        t1=Testcase_Result.get_avg_runtime_performance(run1)
        t2=Testcase_Result.get_avg_runtime_performance(run2)
        return t2-t1
          
   

    @classmethod
    def get_fastest_run_for_student(self,name, keylist):
        logging.debug(name)
        results=dbm.session.query(Run, sub.Submission)\
            .join(sub.Submission).join(stud.Student)\
            .filter(Run.passed==True)\
            .filter(sub.Submission.is_fast==True, stud.Student.name==name).all()
        performance=list()
        logging.debug(results)
        for run,submission in results:
            time=Testcase_Result.get_avg_runtime_performance(run, keylist)
            space=Testcase_Result.get_avg_space_performance(run, keylist)
            if run.manual_overwrite_passed!=True:
                performance.append([run, submission, time, space])
        logging.debug(performance)
        if len(performance)>0:
            fastest_run=performance[0]
            fastest_time=Testcase_Result.get_avg_runtime_performance(run, keylist)
            for r in performance:
                r_time=Testcase_Result.get_avg_runtime_performance(run, keylist)
                if r_time<fastest_time:
                    fastest_run=r
                    fastest_time=r_time
            return fastest_run
        return None
        

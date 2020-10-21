from sqlalchemy import *
from alchemy.base import Base
from sqlalchemy.orm import relationship

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



    testcase_results = relationship("Valgrind_Output", uselist=False, backref="Testcase_Result.id")
   
    def __init__(self, run_id, testcase_id):   
        self.run_id = run_id
        self.testcase_id=testcase_id



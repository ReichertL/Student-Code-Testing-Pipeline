from sqlalchemy import *
from alchemy.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression


class Valgrind_Output(Base):
    __tablename__ = 'Valgrind_Output'
   
    id = Column(Integer, primary_key =  True)
    testcase_result_id=Column(Integer,  ForeignKey("Testcase_Result.id"),nullable=False)
    ok=Column(Boolean, default=False,server_default=expression.false())               #
    invalid_read_count=Column(Integer,default=0,server_default='0')    #
    invalid_write_count=Column(Integer, default=0, server_default='0')  #

    #in use at exit
    in_use_at_exit_bytes=Column(Integer)
    in_use_at_exit_blocks=Column(Integer)

    #total heap usage
    total_heap_usage_allocs=Column(Integer)
    total_heap_usage_frees=Column(Integer)    
    total_heap_usage_bytes=Column(Integer)

    #leak summary
    definitely_lost_bytes=Column(Integer)
    definitely_lost_blocks=Column(Integer)
    indirectly_lost_bytes=Column(Integer)
    indirectly_lost_blocks=Column(Integer)
    possibly_lost_bytes=Column(Integer)
    possibly_lost_blocks=Column(Integer)
    still_reachable_bytes=Column(Integer)
    still_reachable_blocks=Column(Integer)
    suppressed_bytes=Column(Integer)
    suppressed_blocks=Column(Integer)

    #error summary
    summary_errors=Column(Integer)
    summary_contexts=Column(Integer)
    summary_suppressed_bytes=Column(Integer)
    summary_suppressed_blocks=Column(Integer)



    def __init__(self, testcase_result_id):   
        self.testcase_result_id = testcase_result_id








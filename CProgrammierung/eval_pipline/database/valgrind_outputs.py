"""
SQL Alchemy classed used to create table "Valgrind_Output". Also contains functions that query the database for table "Valgrind_Output".
"""

from sqlalchemy import *
from database.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression
import database.database_manager as dbm

class Valgrind_Output(Base):
    __tablename__ = 'Valgrind_Output'
    # Columns for the table "Valgrind_Output"
    id = Column(Integer, primary_key =  True)
    testcase_result_id=Column(Integer,  ForeignKey("Testcase_Result.id"),nullable=False)
    ok=Column(Boolean, default=False,server_default=expression.false())               #
    invalid_read_count=Column(Integer,default=0,server_default='0')    #
    invalid_write_count=Column(Integer, default=0, server_default='0')  #

    #in use at exit
    in_use_at_exit_bytes=Column(Integer)
    #in_use_at_exit_blocks=Column(Integer)

    #total heap usage
    total_heap_usage_allocs=Column(Integer)
    total_heap_usage_frees=Column(Integer)    
    total_heap_usage_bytes=Column(Integer)

    #leak summary
    definitely_lost_bytes=Column(Integer)
    #definitely_lost_blocks=Column(Integer)
    indirectly_lost_bytes=Column(Integer)
    #indirectly_lost_blocks=Column(Integer)
    possibly_lost_bytes=Column(Integer)
    #possibly_lost_blocks=Column(Integer)
    still_reachable_bytes=Column(Integer)
    #still_reachable_blocks=Column(Integer)
    suppressed_bytes=Column(Integer)
    #suppressed_blocks=Column(Integer)

    #error summary
    summary_errors=Column(Integer)
    #summary_contexts=Column(Integer)
    summary_suppressed_errors=Column(Integer)
    #summary_suppressed_blocks=Column(Integer)



    def __init__(self, testcase_result_id):   
        self.testcase_result_id = testcase_result_id

    @classmethod
    def create_or_get(self, tcr_id):
        """
        Creates a new Valgrind_Output in table "Valgrind_Output" or returns the existing entry with the same testcase result ID.
        Parameters:
            tcr_id (int): ID of a Testcase_Result in table "Testcase_Result"
        Returns:
            Valgrind_Output object
        """
        output=dbm.session.query(Valgrind_Output).filter(Valgrind_Output.testcase_result_id==tcr_id).first()
        if output==None:
            output=Valgrind_Output(tcr_id)
            dbm.session.add(output)
            dbm.session.commit()
            return output
        return output
    






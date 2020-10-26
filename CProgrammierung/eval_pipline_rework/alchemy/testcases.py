import logging

from sqlalchemy import *
from alchemy.base import Base 
from sqlalchemy.orm import relationship

import alchemy.database_manager as dbm

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)


class Testcase(Base):
    __tablename__ = 'Testcase'
    type_options= ["GOOD","BAD","PERFORMANCE", "BAD_OR_OUTPUT", "EXTRA"]    


    id = Column(Integer, primary_key =  True)
    path = Column(String, nullable=False)
    valgrind_needed = Column(Boolean,default=True)
    short_id = Column(String,nullable=False, unique=True)
    description = Column(String,nullable=False)
    hint = Column(String,nullable=False)
    type = Column(String,nullable=False)
  
    test_case_results = relationship("Testcase_Result")
   
    def __init__(self, path, short_id, description, hint, type):   
        if type not in self.type_options:
            raise TypeError("Type of Testcase does not have an allowed value. Was "+str(type)+" but only "+str(self.type_options)+ " are allowed." )
        self.path = path
        self.short_id = short_id
        self.description = description
        self.hint = hint
        self.type = type

    def __repr__(self):
        return ("(Testcase: " + str(self.id) + ","+
                                str(self.path) + "," + 
                                str(self.short_id) + ","+ 
                                str(self.description) + "," +
                                str(self.hint) + ","+
                                str(self.type)+")")
    

    def update( self,testcase):
        self.path=testcase.path
        self.valgrind_needed=testcase.valgrind_needed
        self.short_id=testcase.short_id
        self.description=testcase.description
        self.hint=testcase.hint
        self.type=testcase.type
        

        
    @classmethod    
    def get_all_bad (self):
        testcases=dbm.session.query(Testcase).filter(Testcase.type=="BAD").all()
        return testcases        

       
    @classmethod    
    def get_all_good(self):
        testcases=dbm.session.query(Testcase).filter_by(type="GOOD").all()
        return testcases    

    @classmethod    
    def get_all_bad_or_output(self):
        testcases=dbm.session.query(Testcase).filter_by(type="BAD_OR_OUTPUT").all()
        return testcases   
        
    @classmethod        
    def get_all_performance(self):
        testcases=dbm.session.query(Testcase).filter_by(type="PERFORMANCE").all()
        return testcases    

    @classmethod    
    def create_or_update(self,new_testcase):
        #logging.debug("create or update")
        tc_exists=dbm.session.query(Testcase).filter(Testcase.short_id==new_testcase.short_id,Testcase.path==new_testcase.path, Testcase.valgrind_needed==new_testcase.valgrind_needed, Testcase.description==new_testcase.description, Testcase.hint==new_testcase.hint, Testcase.type==new_testcase.type).count()

        if tc_exists==0:
            similar=dbm.session.query(Testcase).filter(Testcase.short_id==new_testcase.short_id).first()
            if not (similar==None):
                similar.update(new_testcase)
                dbm.session.commit()
            else:
                dbm.session.add(new_testcase)
                dbm.session.commit()            
            logging.info("New testcase inserted or altered one upgedated.")





import logging

from sqlalchemy import *
from database.base import Base 
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression

import database.database_manager as dbm

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)


class Testcase(Base):
    __tablename__ = 'Testcase'
    type_options= ["GOOD","BAD","PERFORMANCE", "BAD_OR_OUTPUT", "EXTRA"]    


    id = Column(Integer, primary_key =  True)
    path = Column(String, nullable=False)
    valgrind_needed = Column(Boolean,default=True,server_default=expression.true())
    short_id = Column(String,nullable=False, unique=True)
    description = Column(String,nullable=False)
    hint = Column(String,nullable=False)
    type = Column(String,nullable=False)
  
    test_case_results = relationship("Testcase_Result")
   
    def __init__(self, path, short_id, description, hint, type, rlimit):   
        if type not in self.type_options:
            raise TypeError("Type of Testcase does not have an allowed value. Was "+str(type)+" but only "+str(self.type_options)+ " are allowed." )
        self.path = path
        self.short_id = short_id
        self.description = description
        self.hint = hint
        self.rlimit = rlimit
        self.type = type

    def __repr__(self):
        return ("(Testcase: " + str(self.id) + ","+
                                str(self.path) + "," + 
                                str(self.short_id) + ","+ 
                                str(self.description) + "," +
                                str(self.hint) + ","+
                                str(self.rlimit) + ","+
                                str(self.type)+")")
    

    def update( self,path, short_id, description, hint, type, valgrind_needed, rlimit):
        self.path=path
        self.valgrind_needed=valgrind_needed
        self.short_id=short_id
        self.description=description
        self.hint=hint
        self.type=type
        self.rlimit=rlimit
        

    @classmethod    
    def get_all(cls):
        testcases=dbm.session.query(Testcase).all()
        return testcases  

        
    @classmethod    
    def get_all_bad (cls):
        testcases=dbm.session.query(Testcase).filter(Testcase.type=="BAD").all()
        return testcases        

       
    @classmethod    
    def get_all_good(cls):
        testcases=dbm.session.query(Testcase).filter_by(type="GOOD").all()
        return testcases    

    @classmethod    
    def get_all_bad_or_output(cls):
        testcases=dbm.session.query(Testcase).filter_by(type="BAD_OR_OUTPUT").all()
        return testcases   
        
    @classmethod        
    def get_all_performance(cls):
        testcases=dbm.session.query(Testcase).filter_by(type="PERFORMANCE").all()
        return testcases    

    @classmethod    
    def create_or_update(cls,path, short_id, description, hint, type, valgrind=True,rlimit=None):
        #logging.debug("create or update")
        tc_exists=dbm.session.query(Testcase).filter(Testcase.short_id==short_id,Testcase.path==path, Testcase.valgrind_needed==valgrind, Testcase.description==description, Testcase.hint==hint, Testcase.type==type, Testcase.rlimit==rlimit).count()
        if tc_exists==0:
            similar=dbm.session.query(Testcase).filter(Testcase.short_id==short_id).first()
            if not (similar==None):
                similar.update(path, short_id, description, hint, type, valgrind,rlimit)
                dbm.session.commit()
            else:
                new_testcase=Testcase(path, short_id, description, hint, type, rlimit)
                new_testcase.valgrind_needed=valgrind
                dbm.session.add(new_testcase)
                dbm.session.commit()            
            logging.info("New testcase inserted or altered one upgedated.")

    @classmethod
    def get_by_ID(id):
        testcase=dbm.session.query(Testcase).filter(Testcase.id==id).first()
        return testcases
            
    @classmethod
    def get_by_shortID(short_id):
        testcase=dbm.session.query(Testcase).filter(Testcase.short_id==short_id).first()
        return testcases

    
    

from sqlalchemy import *
from alchemy.base import Base 
from sqlalchemy.orm import relationship


class Testcase(Base):
    __tablename__ = 'Testcase'
    type_options= ["GOOD","BAD","PERFORMANCE", "BAD_OR_OUTPUT", "EXTRA"]    


    id = Column(Integer, primary_key =  True)
    path = Column(String, nullable=False)
    valgrind_needed = Column(Boolean)
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

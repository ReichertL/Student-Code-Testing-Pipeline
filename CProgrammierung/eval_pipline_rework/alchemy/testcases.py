from sqlalchemy import *
from alchemy.base import Base 
from sqlalchemy.orm import relationship


class Testcase(Base):
    __tablename__ = 'Testcase'
   
    id = Column(Integer, primary_key =  True)
    path = Column(String, nullable=False)
    valgrind_needed = Column(Integer)
    short_id = Column(String,nullable=False)
    description = Column(String,nullable=False)
    hint = Column(String,nullable=False)
    type = Column(String,nullable=False)
  
    test_case_results = relationship("Testcase_Result")
   
    def __init__(self, path, short_id, description, hint, type):   
        self.path = path
        self.short_id = short_id
        self.description = description
        self.hint = hint
        self.type = type
    


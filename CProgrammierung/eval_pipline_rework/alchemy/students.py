from sqlalchemy import *
from alchemy.base import Base 
from sqlalchemy.orm import relationship


class Student(Base):
   __tablename__ = 'Student'
   
   id = Column(Integer, primary_key =  True)
   name = Column(String, nullable=False)
   moodle_id = Column(Integer,nullable=False)
   matrikel_nr = Column(Integer)
   grade = Column(String)
   last_mailed = Column(DateTime)
   abtestat_time = Column(DateTime)

   submissions = relationship("Submission", backref="Student.id")
   
   def __init__(self, name, moodle_id):   
        self.name = name
        self.moodle_id=moodle_id      

        
   def __repr__(self):
        return ("(Student: " + str(self.id) + "," + str(self.name)+")")




from sqlalchemy import *
from alchemy.base import Base
from sqlalchemy.orm import relationship

class Submission(Base):
   __tablename__ = 'Submission'
   
   id = Column(Integer, primary_key =  True)
   student_id=Column(Integer,  ForeignKey("Student.id"),nullable=False)
   submission_time = Column(DateTime)
   submission_path = Column(String, nullable=False)
   is_checked = Column(Boolean, default=False)
   is_fast = Column(Boolean)

   runs = relationship("Run", backref="Submission.id")   

   def __init__(self, student_id, submission_path):   
      self.student_id = student_id
      self.submission_path=submission_path
        
   def __repr__(self):
        return ("(Submission: " + str(self.id) + "," + 
                                str(self.student_id) + "," + 
                                str(self.submission_time) + "," + 
                                str(self.submission_path) + "," + 
                                str(self.is_checked) + "," + 
                                str(self.is_fast) +")")





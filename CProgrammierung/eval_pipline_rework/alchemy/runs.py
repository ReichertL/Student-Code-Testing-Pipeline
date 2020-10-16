from sqlalchemy import *
from alchemy.base import Base
from sqlalchemy.orm import relationship

class Run(Base):
   __tablename__ = 'Run'
   
   id = Column(Integer, primary_key =  True)
   submission_id=Column(Integer,  ForeignKey("Submission.id"),nullable=False)
   compilation_id=Column(Integer,  ForeignKey("Compilation.id"),nullable=False)
   run_time = Column(DateTime)
   manual_passed = Column(Boolean)

   #testcase_results = relationship("Compilation", backref="Submission.id")
   
   def __init__(self, student_id, submission_path):   
      self.student_id = student_id
      self.submission_path=submission_path

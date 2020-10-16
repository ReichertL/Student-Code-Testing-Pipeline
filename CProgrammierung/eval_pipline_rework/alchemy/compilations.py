from sqlalchemy import *
from alchemy.base import Base
from sqlalchemy.orm import relationship

class Compilation(Base):
    __tablename__ = 'Compilation'
   
    id = Column(Integer, primary_key =  True)
    submission_id=Column(Integer,  ForeignKey("Submission.id"),nullable=False)
    careless_flag = Column(Boolean)
    return_code = Column(Integer)
    command_line=Column(String, nullable=False)
    compiler_output=Column(String, nullable=False)

    runs = relationship("Run", uselist=False,backref="Run.id")   
   
    def __init__(self, submission_id, command_line,compiler_output):   
        self.submission_id = student_id
        self.command_line=command_lines
        self.compiler_output=compiler_output

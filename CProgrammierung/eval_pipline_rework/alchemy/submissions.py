import logging

from sqlalchemy import *
from alchemy.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression, or_


import alchemy.database_manager as dbm
from alchemy.students import Student


FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)

class Submission(Base):
    __tablename__ = 'Submission'
   
    id = Column(Integer, primary_key =  True)
    student_id=Column(Integer,  ForeignKey("Student.id"),nullable=False)
    submission_time = Column(DateTime)
    submission_path = Column(String, nullable=False)
    is_checked = Column(Boolean, default=False,server_default=expression.false())
    is_fast = Column(Boolean)
    student_notified=Column(Boolean)
    notification_time = Column(DateTime)


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

    @classmethod
    def insert_submission(cls,student, path, time):
        count=dbm.session.query(Submission).filter(Submission.student_id==student.id, Submission.submission_path==path, Submission.submission_time==time).count()
        
        if count==0:
            sub=Submission(student.id, path)
            sub.submission_time=time
            dbm.session.add(sub)
            dbm.session.commit()

    @classmethod    
    def get_not_checked(cls):
        submissions=dbm.session.query(Submission,Student).join(Student)\
        .filter(or_(Submission.is_checked==False, Submission.is_checked==None)).all()
        return submissions

    @classmethod            
    def get_not_checked_for_name(cls,student_name):
        submissions_student=dbm.session.query(Submission,Student).join(Student).filter(Student.name==student_name, Submission.is_checked==False).all()
        return submissions_student

    @classmethod        
    def get_all_for_name(cls,student_name):
        submissions_student=dbm.session.query(Submission,Student).join(Student).filter(Student.name==student_name).all()
        return submissions_student

    @classmethod            
    def get_last_for_name(cls,name):
        results=dbm.session.query(Submission,Student).join(Student)\
            .filter(Submission.is_checked==True,Student.name==name).order_by(Submission.submission_time.desc()).first()
        return results

    @classmethod
    def get_sumbissions_for_notification(cls):
        results=dbm.session.query(Student, Submission).join(Submission, Submission.student_id==Student.id).filter(Submission.is_checked==True)\
            .filter(or_(Submission.student_notified==False,Submission.student_notified==None)).all()
        return results

    @classmethod    
    def get_sumbissions_for_notification_by_name(cls,name):
        results=dbm.session.query(Student, Submission).join(Submission, Submission.student_id==Student.id).filter(Submission.is_checked==True, Student.name==name).\
            filter(or_(Submission.student_notified==False,Submission.student_notified==None )).all()
        return results


        
        
        

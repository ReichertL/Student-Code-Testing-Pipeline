from sqlalchemy import *
from alchemy.base import Base 
from sqlalchemy.orm import relationship
from util.colored_massages import Warn


import alchemy.submissions 
import alchemy.database_manager as dbm


class Student(Base):
    __tablename__ = 'Student'
   
    id = Column(Integer, primary_key =  True)
    name = Column(String, nullable=False, unique=True)
    moodle_id = Column(Integer,nullable=False, unique=True)
    matrikel_nr = Column(Integer, unique=True)
    grade = Column(String)
    last_mailed = Column(DateTime)
    abtestat_time = Column(DateTime)

    submissions = relationship("Submission", backref="Student.id")
   
    def __init__(self, name, moodle_id):   
        self.name = name
        self.moodle_id=moodle_id      

    
    @classmethod
    def __repr__(self):
        return ("(Student: " + str(self.id) + "," + str(self.name)+")")


    @classmethod
    def is_empty(self):
        result = dbm.session.query(Student).all() 
        if (len(result)<1):       
            return True
        return False
    
    @classmethod
    def get_students_all(self):
        result = dbm.session.query(Student).all()      
        return result
        
    @classmethod
    def get_or_insert(self,name,moodle_id):
        student=self.get_student_by_name(name)
        if student==None:
            Warn("Student with name "+str(name)+" did not exist. An database entrie is now created.")
            student_new=Student(name,moodle_id )
            dbm.session.add(student_new)
            dbm.session.commit()
            return student_new
        return student

    @classmethod
    def get_student_by_name(self, student_name):
        result = dbm.session.query(Student).filter_by(name=student_name).order_by(Student.id).first()      
        return result

    @classmethod
    def get_student_by_moodleID(self, student_moodle_id):
        result = dbm.session.query(Student).filter_by(moodle_id=student_moodle_id).order_by(Student.id).first()      
        return result

    @classmethod
    def get_student_by_submission(self,sub):
        result=dbm.session.query(Student).join(Submission).filter(Student.id==sub.student_id).first()
        return result

    @classmethod
    def is_student_passed(self,name):
        results=dbm.session.query(Student).join(Submission, Submission.student_id==Student.id).join(Run, Run.submission_id==Submission.id).filter(Run.passed==True,Student.name==name).count()
        if results >0:
            return True
        return False

    @classmethod
    def get_students_passed(self):
        #This syntax also returns the other colums: 
        #results=dbm.session.query(Student,Submission, Run).join(Submission, Submission.student_id==Student.id).join(Run, Run.submission_id==Submission.id).filter_by(passed=True).group_by(Student.name).all()
        results=dbm.session.query(Student).join(Submission, Submission.student_id==Student.id).join(Run, Run.submission_id==Submission.id).filter_by(passed=True).group_by(Student.name).all()
        return results
        
    @classmethod
    def get_students_not_passed(self):
        results=dbm.session.query(Student).join(Submission, Submission.student_id==Student.id).join(Run, Run.submission_id==Submission.id).filter(Run.passed==False).group_by(Student.name).all()
        return results

    @classmethod
    def get_sumbissions_students_to_notify(self):
        results=dbm.session.query(Student, Submission).join(Submission, Submission.student_id==Student.id).filter(Submission.is_checked==True, Submission.student_notified==False).all()
        return results

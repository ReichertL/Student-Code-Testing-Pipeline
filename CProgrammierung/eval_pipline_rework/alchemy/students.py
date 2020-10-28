from sqlalchemy import *
from alchemy.base import Base 
from sqlalchemy.orm import relationship
from util.colored_massages import Warn

import alchemy.runs as r
import alchemy.submissions as sub
import alchemy.database_manager as dbm


class Student(Base):
    __tablename__ = 'Student'
   
    id = Column(Integer, primary_key =  True)
    name = Column(String, nullable=False, unique=True)
    moodle_id = Column(Integer,nullable=False, unique=True)
    matrikel_nr = Column(Integer, unique=True)
    grade = Column(String)
    abtestat_time = Column(DateTime)

    submissions = relationship("Submission", backref="Student.id")
   
    def __init__(self, name, moodle_id):   
        self.name = name
        self.moodle_id=moodle_id      

    
    def __repr__(self):
        return ("(Student: " + str(self.id) + "," + str(self.name)+")")


    @classmethod
    def is_empty(cls):
        result = dbm.session.query(Student).all() 
        if (len(result)<1):       
            return True
        return False
    
    @classmethod
    def get_students_all(cls):
        result = dbm.session.query(Student).all()      
        return result
        
    @classmethod
    def get_or_insert(cls,name,moodle_id):
        student=cls.get_student_by_name(name)
        if student==None:
            #Warn("Student with name "+str(name)+" did not exist. An database entrie is now created.")
            student_new=Student(name,moodle_id )
            dbm.session.add(student_new)
            dbm.session.commit()
            return student_new
        return student

    @classmethod
    def get_student_by_name(cls, student_name):
        result = dbm.session.query(Student).filter_by(name=student_name).order_by(Student.id).first()      
        return result

    @classmethod
    def get_student_by_moodleID(cls, student_moodle_id):
        result = dbm.session.query(Student).filter_by(moodle_id=student_moodle_id).order_by(Student.id).first()      
        return result

    @classmethod
    def get_student_by_submission(cls,submission):
        result=dbm.session.query(Student).join(sub.Submission).filter(Student.id==submission.student_id).first()
        return result

    @classmethod
    def is_student_passed(cls,name):
        results=dbm.session.query(Student).join(sub.Submission, sub.Submission.student_id==Student.id).join(r.Run, r.Run.submission_id==sub.Submission.id).filter(r.Run.passed==True,Student.name==name).count()
        if results >0:
            return True
        return False

    @classmethod
    def get_students_passed(cls):
        #This syntax also returns the other colums: 
        #results=dbm.session.query(Student,Submission, Run).join(Submission, Submission.student_id==Student.id).join(Run, Run.submission_id==Submission.id).filter_by(passed=True).group_by(Student.name).all()
        results=dbm.session.query(Student).join(sub.Submission, sub.Submission.student_id==Student.id).join(r.Run, r.Run.submission_id==sub.Submission.id).filter_by(passed=True).group_by(Student.name).all()
        return results
        
    @classmethod
    def get_students_not_passed(cls):
        results=dbm.session.query(Student).join(sub.Submission, sub.Submission.student_id==Student.id).join(r.Run, r.Run.submission_id==sub.Submission.id).filter(r.Run.passed==False).group_by(Student.name).all()
        return results

    @classmethod
    def get_abtestat_done(cls):
        result = dbm.session.query(Student).filter_by(grade="2").all()      
        return result


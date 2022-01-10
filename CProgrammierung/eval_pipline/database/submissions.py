"""
SQL Alchemy classed used to create table "Submission". Also contains functions that query the database for table "Submission".
"""

import logging
from sqlalchemy import *
from database.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression, or_
import database.database_manager as dbm
from database.students import Student
from database.runs import Run


FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)

class Submission(Base):
    __tablename__ = 'Submission'
    # Columns for the table "Submission"
    id = Column(Integer, primary_key =  True)
    student_id=Column(Integer,  ForeignKey("Student.id"),nullable=False)
    submission_time = Column(DateTime)
    submission_path = Column(String, nullable=False)
    is_checked = Column(Boolean, default=False,server_default=expression.false())
    is_fast = Column(Boolean)
    student_notified=Column(Boolean)
    notification_time = Column(DateTime)

    # foreign key relationship with table "Run"
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
        """
        Insert new sumbission in table "Submission" if it does not already exist. 
        Check student_id, submission_path and submission_time time to figure out if the submission already exists.
        
        Parameters:
            student (Student object)
            path (string): path to submission
            time (DateTime object): Format expected is %Y_%m_%d_%H_%M_%S . In the database_integrator it is the modification time of the file.
        
        Returns:
            Nothing.
        """
        count=dbm.session.query(Submission).filter(Submission.student_id==student.id, Submission.submission_path==path, Submission.submission_time==time).count()
        
        if count==0:
            sub=Submission(student.id, path)
            sub.submission_time=time
            dbm.session.add(sub)
            dbm.session.commit()

    @classmethod    
    def get_not_checked(cls):
        """
        Get all submissions from table "Submission" which have not yet been checked.
        Parameters: None
        Returns:
            List of pairs each containing a Submission and  a Student objects for which is_checked is not True.
        
        """
        submissions=dbm.session.query(Submission,Student).join(Student)\
        .filter(Submission.is_checked!=True).all()
        return submissions

    @classmethod            
    def get_not_checked_for_name(cls,student_name):
        """
        Get all submissions that have not been checked for a specific student using the students name.
        Parameters:
            student_name (string)
        Returns:
            List of pairs each containing a Submission and  a Student objects
        
        """
        submissions_student=dbm.session.query(Submission,Student).join(Student).filter(Student.name==student_name, Submission.is_checked!=True).all()
        return submissions_student

    @classmethod        
    def get_all_for_name(cls,student_name):
        """
        Get all submission for a specific student.
        Parameters: 
            student_name (string)
        Returns:
            List of pairs each containing a Submission and  a Student objects
        
        """
        submissions_student=dbm.session.query(Submission,Student).join(Student).filter(Student.name==student_name).all()
        return submissions_student

    @classmethod            
    def get_last_for_name(cls,name):
        """
        Get last submission for a specific student that has already been checked.
        Parameters: 
            name (string)
        Returns:
            List of pairs each containing a Submission and  a Student objects
        
        """
        
        results=dbm.session.query(Submission,Student).join(Student)\
            .filter(Submission.is_checked==True,Student.name==name).order_by(Submission.submission_time.desc()).first()
        return results

    @classmethod            
    def get_passed_for_name(cls,name):
        """
        Get all submissions for a specific student which have at least one run that is passed. Ordered by submission_time.
        Parameters: 
            name (string)
        Returns:
            List of Submission objects.
        
        """
        
        results=dbm.session.query(Submission).join(Student).join(Run,Run.submission_id==Submission.id)\
            .filter(Run.passed==True, Student.name==name).order_by(Submission.submission_time.desc())
        return results
    
    @classmethod    
    def is_passed(cls, sub):
        """
        Retruns for a submission if it is passed. WARNING : Might not work. Use corresponding function in Run.py instead.
        Parameters:
            sum (Submission object)
        Retruns:
            Boolean
        """
        results=dbm.session.query(Submission).join(Run, Run.submission_id==sub.id).filter(Run.passed==True).count()
        if results >0:
            return True
        return False

    @classmethod
    def get_sumbissions_for_notification(cls):
        """
        Get all submission which are already checked and for which a notification still has to be sent to the student via Moodle.
        Parameters: None
        Returns:
            List of pairs each containing a Submission and  a Student objects
        """
        results=dbm.session.query(Student, Submission).join(Submission, Submission.student_id==Student.id).filter(Submission.is_checked==True)\
            .filter(or_(Submission.student_notified==False,Submission.student_notified==None)).all()
        return results

    @classmethod    
    def get_sumbissions_for_notification_by_name(cls,name):
        """
        Get all submission by a specific student which are already checked, but no notification has been send out via Moodle.
        Parameters: 
            name (string) : Name of student to be notified
        Returns:
            List of pairs each containing a Submission and  a Student objects
        """
        results=dbm.session.query(Student, Submission).join(Submission, Submission.student_id==Student.id).filter(Submission.is_checked==True, Student.name==name).\
            filter(or_(Submission.student_notified==False,Submission.student_notified==None )).all()
        return results


        
        
        

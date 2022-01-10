"""
SQL Alchemy classed used to create table "Student". Also contains functions that query the database for table "Student".
"""


import logging
from sqlalchemy import *
from database.base import Base 
from sqlalchemy.orm import relationship
from util.colored_massages import Warn
import database.runs as r
import database.submissions as sub
import database.database_manager as dbm

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)

class Student(Base):
    __tablename__ = 'Student'
    # Columns for  the table "Student"
    id = Column(Integer, primary_key =  True)
    name = Column(String, nullable=False, unique=True)
    moodle_id = Column(Integer,nullable=False, unique=True)
    matrikel_nr = Column(Integer, unique=True)
    grade = Column(String)
    abtestat_time = Column(DateTime)

    # forgein key relationship to table Submission
    submissions = relationship("Submission", backref="Student.id")
   
    def __init__(self, name, moodle_id):  
        self.name = name
        self.moodle_id=moodle_id      
        
    def __repr__(self):
        return ("(Student: " + str(self.id) + "," + str(self.name)+")")

    @classmethod
    def is_empty(cls):
        """
        Check if the "Student" table is empty. 
        Parameters: None
        Returns: 
            Boolean
        """
        result = dbm.session.query(Student).all() 
        if (len(result)<1):       
            return True
        return False
    
    @classmethod
    def get_students_all(cls):
        """
        Gets a list of all students in the database. If the script has been run already, the table contains all people enrolled in the moodle course.
        Parameters: None
        Returns:
            List of Student objects or None
        """
        result = dbm.session.query(Student).all()      
        return result
        
    @classmethod
    def get_or_insert(cls,name,mid):
        """
        Insert a new student into the table "Student" or get the corresponding Student object if the student aready exists. 
        First tries to find student with name, then with their moodle ID.
        If there are möultiple students with the same name, the first one is selected.
        Parameters:
            name (string): Name of student.
            mid (int): Moodle ID of student.
            
        Returns:
            Student object corresponding to this student (either form the database or a newly created one)
        
        """
        student=cls.get_student_by_name(name)
        if student in [None, [],[[]]]:
            student = dbm.session.query(Student).filter_by(moodle_id=mid).order_by(Student.id).first()      
        if student in [None, [],[[]]]:
            #Warn("Student with name "+str(name)+" did not exist. An database entrie is now created.")
            student_new=Student(name,mid )
            dbm.session.add(student_new)
            dbm.session.commit()
            return student_new
        if type(student)==list:
            logging.error(f"Student was not found but there are students with similar names. Selecting {student[0].name}")   
            return student[0]
        return student

    @classmethod
    def get_student_by_name(cls, student_name):
        """
        Gets the student only using the students name. If no student with the exact name was found, at most 5 other students with a similar name are returned.
        Parameters:
            student_name (string): Name of a student
        Returns:
            student object or list of student objects 
            or None  if no similar entries are found
        
        """
        result = dbm.session.query(Student).filter_by(name=student_name).order_by(Student.id).first()      
        if result==None:
            needle="%{}%".format(student_name)
            result = dbm.session.query(Student).\
			filter(Student.name.like(needle)).\
			limit(5).all()
        return result

    @classmethod
    def get_student_by_moodleID(cls, student_moodle_id):
        """
        Gets student based on moodle ID.
        Parameters:
            student_moodle_id (int): Moodle ID of student
        Returns:
            student object or None
        """
        result = dbm.session.query(Student).filter_by(moodle_id=student_moodle_id).order_by(Student.id).first()      
        return result

    @classmethod
    def get_student_by_submission(cls,submission):
        """
        Gets student  who submitted this submission.
        Parameters:
            submission (Submission object): submission handed in by student
        Returns:
            student object or None
        """
        result=dbm.session.query(Student).join(sub.Submission).filter(Student.id==submission.student_id).first()
        return result

    @classmethod
    def is_student_passed(cls,name):
        """
        Check if a student is passed.
        Parameters:
            name (string): Name of student
        Returns:
            Boolean
        """
        results=dbm.session.query(Student).join(sub.Submission, sub.Submission.student_id==Student.id).join(r.Run, r.Run.submission_id==sub.Submission.id).filter(r.Run.passed==True,Student.name==name).count()
        if results >0:
            return True
        return False

    @classmethod
    def get_students_passed(cls):
        """
        Get a list of all students that have passed. 
        Parameters: None
        Returns:
            List of Student objects where the student has at least one submissions for which one run is marked as "Passed".
        
        """
        
        #This syntax also returns the other colums: 
        #results=dbm.session.query(Student,Submission, Run).join(Submission, Submission.student_id==Student.id).join(Run, Run.submission_id==Submission.id).filter_by(passed=True).group_by(Student.name).all()
        results=dbm.session.query(Student)\
            .join(sub.Submission, sub.Submission.student_id==Student.id)\
            .join(r.Run,r.Run.submission_id==sub.Submission.id)\
            .filter(r.Run.passed==True).group_by(Student.name).all()
        return results
        
    @classmethod
    def get_students_not_passed(cls):
        """
        Get a list of all students that have not passed yet.
        Parameters: None
        Returns:
            List of Student objects where the student has handed in at least one submission but which do not have a submission with a passed run.
        
        
        """
        passed=cls.get_students_passed()
        submitted_once=dbm.session.query(Student).join(sub.Submission, sub.Submission.student_id==Student.id).group_by(Student.name).all()
        results=list(set(submitted_once) - set(passed))
        #results=dbm.session.query(Student).join(sub.Submission, sub.Submission.student_id==Student.id).join(r.Run, r.Run.submission_id==sub.Submission.id)\
        #.filter(r.Run.passed==False).group_by(Student.name).all()
        return results

    @classmethod
    def get_abtestat_done(cls):
        """
        Get a list of all students that have passed their abtestat.
        Parameters: None
        Returns:
            List of Student objects where grade has value "2".
        """
        result = dbm.session.query(Student).filter_by(grade="2").all()      
        return result


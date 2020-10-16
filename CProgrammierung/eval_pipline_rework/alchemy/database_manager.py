import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship, backref, sessionmaker
from alchemy.base import Base 
from alchemy.students import Student
from alchemy.submissions import Submission
from alchemy.compilations import Compilation
from alchemy.runs import Run
from alchemy.testcases import Testcase
from alchemy.testcase_results import Testcase_Result
from alchemy.valgrind_outputs import Valgrind_Output

class DatabaseManager:

    session =None
      

    def __init__(self):
        engine = create_engine('sqlite:///:memory:', echo = True)
        Base.metadata.create_all(engine, checkfirst=True)      
        Session = sessionmaker(bind = engine)
        self.session = Session()


    def is_empty(self):
        result = self.session.query(Student).all() 
        if (len(result)<1):       
            return True
        return False

    def get_student_by_name(self, student_name):
        """        
         In case of Multiple students with the same name an error might occure. Therefore choosing the one with the lowest id.
        """
        result = self.session.query(Student).filter_by(name=student_name).order_by(Student.id).first()      
        return result

    def get_student_by_moodleID(self, student_moodle_id):
        result = self.session.query(Student).filter_by(moodle_id=student_moodle_id).order_by(Student.id).first()      
        return result

    def insert_submission(student, path, time):
        sub=Submission(student.id, path)
        sub.submission_time=time
        self.session.add(sub)
        self.session.commit()

    def functionality(self):
     
        self.session.add(Student("Laura" , "4544555"))
        self.session.add(Student("Isabell", "93233212"))
        self.session.add(Student("Isabell", "65656565"))
        self.session.commit()
        result = self.session.query(Student).all()
        print(result)        
        st=self.get_student_by_name("Lena")
        #print(st.id, " ", st.name)
        
        #result = session.query(Student).all()
        #for row in result:
        #    print ("id:",row.id," Name: ",row.name)
        #    sub1=Submission(row.id, row.name+"/sub1")
        #    sub2=Submission(row.id, row.name+"/sub2")
        #    session.add(sub1)
        #    session.add(sub2)
       #     session.commit()
        #res2=session.query(Student).filter(Student.name.in_(["Isabell"]))
        #for laura in res2:
        #    for sub in laura.submissions:
        #        print("Submission:", sub.id)
        #    print("Submissions:", laura.submissions)




















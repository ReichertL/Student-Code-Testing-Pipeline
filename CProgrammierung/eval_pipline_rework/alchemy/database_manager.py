import sys
import logging

from util.absolute_path_resolver import resolve_absolute_path
from util.config_reader import ConfigReader
from util.colored_massages import Warn


from sqlalchemy import create_engine, and_, or_
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref, sessionmaker
from alchemy.base import Base 
import alchemy.students 
import alchemy.submissions
import alchemy.runs
import alchemy.testcases 
from alchemy.testcase_results import Testcase_Result
from alchemy.valgrind_outputs import Valgrind_Output

session=None

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)

class DatabaseManager:

      

    def __init__(self):
        p = resolve_absolute_path("/resources/config_database_manager.config")
        configuration = ConfigReader().read_file(str(p))
        db_path=resolve_absolute_path(configuration["DATABASE_PATH"])
        #db_path=":memory:"
        engine = create_engine('sqlite:///'+str(db_path), echo = False)
        Base.metadata.create_all(engine, checkfirst=True)      
        Session = sessionmaker(bind = engine)
        global session
        session = Session()
        logging.info("Database created/accessed:"+str(db_path))





    


 





 
 
    def functionality(self):
        
        stud=Student("Laura" , "4544555")
     
        session.add(stud)
        session.add(Student("Isabell", "93233212"))
        session.add(Student("Mona", "65656565"))
        session.commit()
        
        

        
        sub=Submission(self.get_student_by_name("Laura").id, "submissionlaura1")
        sub.is_checked=True
        session.add(sub)
        sub1=Submission(self.get_student_by_name("Laura").id, "submissionlaura2")
        sub1.is_checked=False
        session.add(sub1)
        sub2=Submission(self.get_student_by_name("Mona").id, "submissionmona1")
        session.add(sub2)
        sub3=Submission(self.get_student_by_name("Laura").id, "submissionlaura3")
        sub3.is_checked=True
        session.add(sub3)
        sub4=Submission(self.get_student_by_name("Isabell").id, "submissionIsabell1")
        sub4.is_checked=True
        session.add(sub4)
        sub5=Submission(self.get_student_by_name("Mona").id, "submissionMona2")
        sub5.is_checked=True
        session.add(sub5)
        #session.bulk_save_objects([sub, sub1,sub2,sub3,sub4,sub5])
        session.commit()

        
        run=Run( sub.id, "execute", 0, "")
        run.passed=True
        session.add(run)
        run1=Run( sub3.id, "execute", 0, "")
        run1.passed=True
        run1.manual_overwrite_passed=True
        session.add(run1)
        run2=Run( sub4.id, "execute", 0, "")
        run2.passed=False
        session.add(run2)
        run3=Run( sub5.id, "execute", 0, "")
        run3.passed=False
        run3.manual_overwrite_passed=True
        session.add(run3)
        session.commit()

        #result= session.query(Submission).all()
        #logging.debug(result)




        #result = session.query(Student).all()
        #print(result)        
        #st=self.get_student_by_name("Lena")
        #print(st.id, " ", st.name)
        
        #result = session.query(Testcase).all()
        #print(len(result))
        #for row in result:
        #    print(row)        
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




















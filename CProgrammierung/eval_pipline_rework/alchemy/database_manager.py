import sys
import logging

from util.absolute_path_resolver import resolve_absolute_path
from util.config_reader import ConfigReader
from util.colored_massages import Warn


from sqlalchemy import create_engine, and_
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref, sessionmaker
from alchemy.base import Base 
from alchemy.students import Student
from alchemy.submissions import Submission
from alchemy.runs import Run
from alchemy.testcases import Testcase
from alchemy.testcase_results import Testcase_Result
from alchemy.valgrind_outputs import Valgrind_Output

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)

class DatabaseManager:

    session =None
      

    def __init__(self):
        p = resolve_absolute_path("/resources/config_database_manager.config")
        configuration = ConfigReader().read_file(str(p))
        db_path=configuration["DATABASE_PATH"]
        #db_path=":memory:"
        engine = create_engine('sqlite:///'+db_path, echo = False)
        Base.metadata.create_all(engine, checkfirst=True)      
        Session = sessionmaker(bind = engine)
        self.session = Session()
        logging.info("Database created/accessed:"+db_path)



    def is_empty(self):
        result = self.session.query(Student).all() 
        if (len(result)<1):       
            return True
        return False
    
    def get_students_all(self):
        result = self.session.query(Student).all()      
        return result
        

    def get_student_by_name(self, student_name):
        result = self.session.query(Student).filter_by(name=student_name).order_by(Student.id).first()      
        return result

    def get_student_by_moodleID(self, student_moodle_id):
        result = self.session.query(Student).filter_by(moodle_id=student_moodle_id).order_by(Student.id).first()      
        return result

    def get_student_by_submission(self,sub):
        result=self.session.query(Student).join(Submission).filter(Student.id==sub.student_id).first()
        #todo:test function
        return result

    def get_students_passed(self):
        #This syntax also returns the other collums: 
        #results=self.session.query(Student,Submission, Run).join(Submission, Submission.student_id==Student.id).join(Run, Run.submission_id==Submission.id).filter_by(passed=True).group_by(Student.name).all()
        results=self.session.query(Student).join(Submission, Submission.student_id==Student.id).join(Run, Run.submission_id==Submission.id).filter_by(passed=True).group_by(Student.name).all()
        return results
        
    def get_students_not_passed(self):
        results=self.session.query(Student).join(Submission, Submission.student_id==Student.id).join(Run, Run.submission_id==Submission.id).filter(Run.passed==False).group_by(Student.name).all()
        return results


    def insert_submission(self,student, path, time):
        sub=Submission(student.id, path)
        sub.submission_time=time
        self.session.add(sub)
        self.session.commit()




    def get_submissions_not_checked(self):
        submissions=self.session.query(Submission).filter_by(is_checked=False).all()
        return submissions
        
    def get_submissions_not_checked_for_name(self,student_name):
        submissions_student=self.session.query(Submission).join(Student).filter(Student.name==student_name, Submission.is_checked==False).all()
        return submissions_student
    
    def get_all_submissions_for_name(self,student_name):
        submissions_student=self.session.query(Submission).join(Student).filter(Student.name==student_name).all()
        return submissions_student

    def run_is_passed(self,r):
        count=self.session.query(Testcase_Result)\
            .join(Valgrind_Output, Valgrind_Output.testcase_result_id==Testcase_Result.id)\
            .filter(Testcase_Result.run_id==r.id, Valgrind_Output.ok==True, Testcase_Result.output_correct==True).count()
        if count==0 and r.compilation_return_code==0:
            return True
        return False

    def run_is_passed_for_testcase_type(self,r,testcase_type):
        if testcase_type not in Testcase.type_options:
            Warn(f'Invalid testcase type requested: '+str(testcase_type))
        count=self.session.query(Testcase_Result)\
                .join(Valgrind_Output,Valgrind_Output.testcase_result_id==Testcase_Result.id)\
                .join(Testcase, Testcase.id==Testcase_Result.testcase_id)\
                .filter_by(run_id=r.id, ok=True, output_correct=True, type=testcase_type)\
                .count()
        if count==0 and r.compilation_return_code==0:
            return True
        return False

    def get_failed_testcases_for_run(self,r, testcase_type): 
        if testcase_type not in Testcase.type_options:
            Warn(f'Invalid testcase type requested: '+str(testcase_type))
        failed_testcases=self.session.query(Testcase_Result, Valgrind_Output)\
                                    .join(Valgrind_Output,Valgrind_Output.testcase_result_id==Testcase_Result.id)\
                                    .join(Testcase, Testcase.id==Testcase_Result.testcase_id)\
                                    .filter_by(id=r.id, type=testcase_type)\
                                    .filter(or_(ok=False, output_correct=False))\
                                    .count()
        return failed_testcases
        

#todo test these
    def get_testcases_bad (self):
        testcases=self.session.query(Testcase).filter(Testcase.type=="BAD").all()
        return testcases        

    def get_testcases_good(self):
        testcases=self.session.query(Testcase).filter_by(type="GOOD").all()
        return testcases    

    def get_testcases_bad_or_output(self):
        testcases=self.session.query(Testcase).filter_by(type="BAD_OR_OUTPUT").all()
        return testcases   
        
    def get_testcases_performance(self):
        testcases=self.session.query(Testcase).filter_by(type="PERFORMANCE").all()
        return testcases    


    def testcase_create_or_update(self,new_testcase):
        #logging.debug("create or update")
        tc_exists=self.session.query(Testcase).filter(Testcase.short_id==new_testcase.short_id,Testcase.path==new_testcase.path, Testcase.valgrind_needed==new_testcase.valgrind_needed, Testcase.description==new_testcase.description, Testcase.hint==new_testcase.hint, Testcase.type==new_testcase.type).count()

        if tc_exists==0:
            similar=self.session.query(Testcase).filter(Testcase.short_id==new_testcase.short_id).first()
            if not (similar==None):
                similar.update(new_testcase)
                self.session.commit()
            else:
                self.session.add(new_testcase)
                self.session.commit()            
            logging.info("New testcase inserted or altered one upgedated.")



    def get_avg_cputime_run(self,r):

        
        avg=self.session.query(func.avg(Testcase_Result.cpu_time)).filter_by(run_id=r.id).scalar()
        return avg

    
    def get_avg_cputime_run_performance(self,r , testcase_type):
        avg=self.session.query(func.avg(Testcase_Result.cpu_time)).join(Testcase).filter(Testcase_Result.run_id==r.id, Testcase.type=="PERFORMANCE" ).scalar()
        return avg
 
    def functionality(self):
        
        stud=Student("Laura" , "4544555")
     
        self.session.add(stud)
        self.session.add(Student("Isabell", "93233212"))
        self.session.add(Student("Mona", "65656565"))
        self.session.commit()
        
        

        
        sub=Submission(self.get_student_by_name("Laura").id, "submissionlaura1")
        sub.is_checked=True
        self.session.add(sub)
        sub1=Submission(self.get_student_by_name("Laura").id, "submissionlaura2")
        sub1.is_checked=False
        self.session.add(sub1)
        sub2=Submission(self.get_student_by_name("Mona").id, "submissionmona1")
        self.session.add(sub2)
        sub3=Submission(self.get_student_by_name("Laura").id, "submissionlaura3")
        sub3.is_checked=True
        self.session.add(sub3)
        sub4=Submission(self.get_student_by_name("Isabell").id, "submissionIsabell1")
        sub4.is_checked=True
        self.session.add(sub4)
        sub5=Submission(self.get_student_by_name("Mona").id, "submissionMona2")
        sub5.is_checked=True
        self.session.add(sub5)
        #self.session.bulk_save_objects([sub, sub1,sub2,sub3,sub4,sub5])
        self.session.commit()

        
        run=Run( sub.id, "execute", 0, "")
        run.passed=True
        self.session.add(run)
        run1=Run( sub3.id, "execute", 0, "")
        run1.passed=True
        run1.manual_overwrite_passed=True
        self.session.add(run1)
        run2=Run( sub4.id, "execute", 0, "")
        run2.passed=False
        self.session.add(run2)
        run3=Run( sub5.id, "execute", 0, "")
        run3.passed=False
        run3.manual_overwrite_passed=True
        self.session.add(run3)
        self.session.commit()

        #result= self.session.query(Submission).all()
        #logging.debug(result)




        #result = self.session.query(Student).all()
        #print(result)        
        #st=self.get_student_by_name("Lena")
        #print(st.id, " ", st.name)
        
        #result = self.session.query(Testcase).all()
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




















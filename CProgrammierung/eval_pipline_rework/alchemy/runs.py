import logging
from functools import cmp_to_key

from sqlalchemy import *
from alchemy.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression


import alchemy.database_manager as dbm
from alchemy.testcase_results import Testcase_Result
from alchemy.valgrind_outputs import Valgrind_Output
from alchemy.testcases import Testcase
import alchemy.submissions as sub

from util.colored_massages import red, yellow, green
from util.htable import table_format

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)

class Run(Base):
    __tablename__ = 'Run'
   
    id = Column(Integer, primary_key =  True)
    submission_id=Column(Integer,  ForeignKey("Submission.id"),nullable=False)
    careless_flag = Column(Boolean, default=False,server_default=expression.false())
    command_line=Column(String, nullable=False)
    compilation_return_code = Column(Integer, nullable=False)
    compiler_output=Column(String, nullable=False)
   
    execution_time = Column(DateTime)
    passed = Column(Boolean, default=False,server_default=expression.false())
    manual_overwrite_passed= Column(Boolean)

    testcase_results = relationship("Testcase_Result", backref="Run.id")
   
    def __init__(self, submission_id, command_line, careless_flag, compilation_return_code,compiler_output):   
        self.submission_id = submission_id
        self.command_line=command_line
        self.careless_flag=careless_flag
        self.compilation_return_code=compilation_return_code
        self.compiler_output=compiler_output


    def __repr__(self):
        return ("(Run: " + str(self.id) + "," + \
                                str(self.submission_id) + "," + \
                                str(self.command_line) + "," + \
                                str(self.compilation_return_code) + "," + \
                                str(self.compiler_output)  +")")




    # use like: f=sys.stdout
    def print_small_stats(self, f):
        output = ''
        if self.compilation_return_code!=0:
            output = output + (red('Compilation failed. '))
            print(output)
            return

        output = output + (green('Compilation successful. '))
        
        failed_bad=len(Testcase_Result.get_failed_bad(self))
        failed_good=len(Testcase_Result.get_failed_good(self))

        if self.passed and self.manual_overwrite_passed:
            failed_bad=0
            failed_good=0
            print(f'This run was manually marked as passed (run.id={self.id})')
            
        failed_bad=len(Testcase_Result.get_failed_bad(self))
        all = len(Testcase.get_all_bad())
        if failed_bad > 0:
            output = output + (red(f'{failed_bad} / {all} bad tests failed. '))
        else:
            output = output + (green(f'0 / {all} bad tests failed. '))

        
        all = len(Testcase.get_all_good())
        if failed_good > 0:
            output = output + (red(f'{failed_good} / {all} good tests failed. '))
        else:
            output = output + (green(f'0 / {all} good tests failed. '))

        print(output, file=f)
        

    # use like: f=sys.stdout
    def print_stats(self, f):
        #map_to_int = lambda test_case_result: 1 if self.passe else 0
        if self.compilation_return_code!=0:
            print(red('compilation failed; compiler errors follow:'), file=f)
            print(hline, file=f)
            print(self.compilation.commandline, file=f)
            print(self.compilation.output, file=f)
            print(hline, file=f)
            return
        if len(self.compiler_output) > 0:
            print(yellow('compilation procudes the following warnings:'), file=f)
            print(hline, file=f)
            print(self.command_line, file=f)
            print(self.compiler_output, file=f)
            print(hline, file=f)
        
        failed_bad=Testcase_Result.get_failed_bad(self)
        failed_good=Testcase_Result.get_failed_good(self)

        if self.passed and self.manual_overwrite_passed:
            failed_bad=[]
            failed_good=[]
            print(f'This run was manually marked as passed (run.id={self.id})')
    
        if len(failed_bad)==0 and self.compilation_return_code==0:
            print(green('All tests concerning malicious input passed.'), file=f)
        else:
            all = len(Testcase.get_all_bad())
            print(red(f'{len(failed_bad)} / {all} tests concerning malicious input failed.')
                  , file=f)
            print(file=f)
            failed_bad.sort(key=lambda x: x.short_id)
            print(table_format(
                '{id} | {valgrind} | {valgrind_rw} | {segfault} | {timeout} | {return} | {err_msg} | {description}',
                self.create_stats(failed_bad),
                titles='auto'), file=f)
            print(file=f)

        if len(failed_good)==0 and self.compilation_return_code==0:
            print(green('All tests concerning good input passed.'), file=f)
        else:
            all = len(Testcase.get_all_good())
            print(red(f'{len(failed_good)} / {all} tests concerning good input failed.')
                  , file=f)
            print(file=f)
            failed_good.sort(key=lambda x: x[1].short_id)
            print(table_format(
                '{id} | {valgrind} | {valgrind_rw} | {segfault} | {timeout} | {return} | {output} | {error_description}',
               self.create_stats(failed_good),
                titles='auto'), file=f)
            print(file=f)




    @classmethod
    def create_stats(cls,results):
        stats=list()       
        for result, testcase, valgrind in results:
            line={'id':str(testcase.short_id)}
            line['valgrind']=str(valgrind.ok) if valgrind!=None else ""
            line['valgrind_rw']= str(valgrind.invalid_read_count+valgrind.invalid_write_count) if valgrind!=None else ""
            line['segfault']=str(result.segfault)
            line['timeout']=str(result.timeout)
            line['return']=str(result.return_code)
            line['output']=str(result.output_correct)
            line['error_description']=str(result.error_msg_quality)
            stats.append(line)
        return stats
   
    @classmethod
    def is_passed(cls,r):
        count=dbm.session.query(Testcase_Result)\
            .join(Valgrind_Output, Valgrind_Output.testcase_result_id==Testcase_Result.id, isouter=True)\
            .filter(Testcase_Result.run_id==r.id, Valgrind_Output.ok!=False, Testcase_Result.output_correct==True).count()
        if count==0 and r.compilation_return_code==0:
            return True
        return False

    @classmethod
    def insert_run(cls,run):
        exists=dbm.session.query(Run).filter(Run.submission_id==run.submission_id, Run.command_line==run.command_line, Run.careless_flag==run.careless_flag).first()
        if exists==None:
            dbm.session.add(run)
            dbm.session.commit()
            return run
        return exists   
    
    @classmethod
    def get_last_for_submission(cls,submission):
        run=dbm.session.query(Run).filter(Run.submission_id==submission.id, Run.passed==True).order_by(Run.execution_time.desc()).first()
        if run==None:
            run=dbm.session.query(Run).filter(Run.submission_id==submission.id).order_by(Run.execution_time.desc()).first()
        return run

    @staticmethod
    def comperator_performance(run1,run2):
        t1=Testcase_Result.get_avg_runtime_performance(run1)
        t2=Testcase_Result.get_avg_runtime_performance(run2)
        return t2-t1
          
   

    @classmethod
    def get_fastest_run_for_student(self,name, keylist):
        results=dbm.session.query(Run, sub.Submission).join(sub.Submission).filter(Run.passed==True, sub.Submission.is_fast==True).all()
        performance=list()
        logging.debug(results)
        for run,submission in results:
            time=Testcase_Result.get_avg_runtime_performance(run, keylist)
            space=Testcase_Result.get_avg_space_performance(run, keylist)
            performance.append([run, submission, time, space])
        if len(performance)>0:
            fastest_run=performance[0]
            fastest_time=Testcase_Result.get_avg_runtime_performance(run, keylist)
            for r in performance:
                r_time=Testcase_Result.get_avg_runtime_performance(run, keylist)
                if r_time<fastest_time:
                    fastest_run=r
                    fastest_time=r_time
            return fastest_run
        return None
        

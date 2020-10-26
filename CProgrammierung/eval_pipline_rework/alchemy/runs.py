import logging

from sqlalchemy import *
from alchemy.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression


import alchemy.database_manager as dbm
from alchemy.testcase_results import Testcase_Result
from alchemy.valgrind_outputs import Valgrind_Output
from alchemy.testcases import Testcase

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
   
    def __init__(self, submission_id, command_line, compilation_return_code,compiler_output):   
        self.submission_id = submission_id
        self.command_line=command_line
        self.compilation_return_code=compilation_return_code
        self.compiler_output=compiler_output


    def __repr__(self):
        return ("(Run: " + str(self.id) + "," + \
                                str(self.submission_id) + "," + \
                                str(self.command_line) + "," + \
                                str(self.compilation_return_code) + "," + \
                                str(self.compiler_output)  +")")

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

        failed_good=Testcase_Result.get_failed_good(self)
        if len(failed_good)==0 and self.compilation_return_code==0:
            print(green('All tests concerning good input passed.'), file=f)
        else:
            all = len(Testcase.get_all_good())
            print(red(f'{len(failed_good)} / {all} tests concerning good input failed.')
                  , file=f)
            print(file=f)
            logging.debug(failed_good)
            failed_good.sort(key=lambda x: x[1].short_id)
            print(table_format(
                '{id} | {valgrind} | {valgrind_rw} | {segfault} | {timeout} | {return} | {output} | {error_description}',
               self.create_stats(failed_good),
                titles='auto'), file=f)
            print(file=f)

    @classmethod
    def create_stats(self,results):
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
        #logging.debug(stats)
        return stats
   
    @classmethod
    def is_passed(self,r):
        count=dbm.session.query(Testcase_Result)\
            .join(Valgrind_Output, Valgrind_Output.testcase_result_id==Testcase_Result.id)\
            .filter(Testcase_Result.run_id==r.id, Valgrind_Output.ok==True, Testcase_Result.output_correct==True).count()
        if count==0 and r.compilation_return_code==0:
            return True
        return False

    @classmethod
    def insert_run(self,r):
        exists=dbm.session.query(Run).filter_by(submission_id=r.submission_id, command_line=r.command_line,careless_flag=r.careless_flag).first()
        if exists==None:
            dbm.session.add(r)
            dbm.session.commit()
            return r
        return exists   
   
   

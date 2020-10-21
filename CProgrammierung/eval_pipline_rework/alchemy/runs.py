from sqlalchemy import *
from alchemy.base import Base
from sqlalchemy.orm import relationship

from util.colored_massages import red, yellow, green
from util.htable import table_format

class Run(Base):
    __tablename__ = 'Run'
   
    id = Column(Integer, primary_key =  True)
    submission_id=Column(Integer,  ForeignKey("Submission.id"),nullable=False)
    careless_flag = Column(Boolean, default=False)
    command_line=Column(String, nullable=False)
    compilation_return_code = Column(Integer, nullable=False)
    compiler_output=Column(String, nullable=False)
   
    execution_time = Column(DateTime)
    passed = Column(Boolean, default=False)
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
    def print_stats(self, f, database_manager):
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
      
        if database_manager.run_is_passed("bad"):
            print(green('All tests concerning malicious input passed.'), file=f)
        else:
            failed_bad=database_manager.get_failed_testcases_for_run("bad")
            failed = len(failed_bad)
            all = len(database_manager.get_testcases_bad())
            print(red(f'{failed} / {all} tests concerning malicious input failed.')
                  , file=f)
            print(file=f)
            failed_bad.sort(key=lambda x: x.short_id)
            print(table_format(
                '{id} | {valgrind} | {valgrind_rw} | {segfault} | {timeout} | {return} | {err_msg} | {description}',
                self.create_stats(failed_bad),
                titles='auto'), file=f)
            print(file=f)

        if database_manager.run_is_passed("good"):
            print(green('All tests concerning good input passed.'), file=f)
        else:
            failed_good=database_manager.get_failed_testcases_for_run("good")
            failed = len(failed_good)
            all = len(database_manager.get_testcases_good())
            print(red(f'{failed} / {all} tests concerning good input failed.')
                  , file=f)
            print(file=f)
            failed_good.sort(key=lambda x: x.short_id)
            print(table_format(
                '{id} | {valgrind} | {valgrind_rw} | {segfault} | {timeout} | {return} | {output} | {description}',
               self.create_stats(failed_good),
                titles='auto'), file=f)
            print(file=f)


    def create_stats(results):
        stats={}        
        for result, valgrind in results:
            stats.append(result.testcase_id, valgrind.ok, 
                    valgrind.invalid_read_count+valgrind.invalid_write_count,
                    result.segfault, result.timeout, result.return_code, result.output_correct, result.error_msg_quality)
   

"""
Implements all functionality needed to run
performance statistics
"""
import os
import logging

from database.testcase_results import Testcase_Result
import database.database_manager as dbm
from database.students import Student
from database.runs import Run

from util.absolute_path_resolver import resolve_absolute_path
from util.config_reader import ConfigReader
from util.htable import table_format


FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)

class PerformanceEvaluator:
    """
    implements a Performance evaluator
    which provides all functionality to run
    Performance evaluation and statistics
    """

    def __init__(self):

        config_path = resolve_absolute_path(
            "/resources/config_performance_evaluator.config")
        self.configuration = ConfigReader() \
            .read_file(os.path.abspath(config_path))

    def evaluate_performance(self, submission, run):
        """
        checks whether a submission is performant based on one run
        :param submission: the respective submission
        :return: None
        """
        performant = True
        metric = Testcase_Result.get_avg_runtime(run)
        if metric > float(self.configuration["THRESHOLD"]):
            performant = False
        if submission.is_fast==False or submission.is_fast==None:
            submission.is_fast = performant
            dbm.session.commit()

    def evaluate_competition(self, run):
        """
        evaluates a submission for the competition
        (a optional metric)
        :param submission: the respective submission
        :return: the average tictoc time
        """
        return Testcase_Result.get_avg_runtime_performace(run)





    def evaluate(self):

        """
        evaluates all students if they had passed
        with regard to their performance
        and prints the results into a file an to console
        :return:None
        """
        key_list=self.configuration["PERFORMANCE_TEST_CASES_TIME"]
        performances = list()
        students = Student.get_students_passed()
        logging.debug(students)
        for student in students:
            fastest= Run.get_fastest_run_for_student(student.name, key_list)
            if fastest!=None:
                run, submission, time, space=fastest
            
                result={'name':student.name, 'mrss':space}
                for key in key_list:
                    testcase_result=Testcase_Result.get_testcase_result_by_run_and_testcase(run.id,testcase_name=key)
                    if not testcase_result==None:
                        result[key]=testcase_result.tictoc
                    else: result[key]=""
                performances.append(result)
        logging.debug(performances)
                
    
        try:
            os.unlink("performances.txt")
        except FileNotFoundError:
            pass

        row_format = ' | '.join(['{name}'] + ['{{{}:.3f}}'.format(col)
                                              for col in
                                              self.configuration[
                                                  "PERFORMANCE_TEST_CASES_TIME"
                                              ]]
                                + ['{mrss:.0f}'])
        for i in range(1, len(key_list)):
            print(f"\nSorted by {key_list[i]}:\n")
            print(table_format(
                # '{name} | {example10} | {example11} |'
                # ' {example12} | {example2001} | {example2002} |'
                # ' {example2003} | {example2004} | {example2005} | {mrss}',
                
                row_format,
                sorted(performances, key=lambda k: float(k[key_list[i]])),
                titles='auto'))

            with open("performances.html", "a+") as file:
                print(f"\nSorted by {key_list[i]}:\n", file=file)
                print(table_format(
                    row_format,
                    sorted(performances,
                           key=lambda k: float(k[key_list[i]])),
                    titles='auto',
                    html=True,
                    highlight=key_list[i]),
                      file=file)
"""
Implements all functionality needed to run
performance statistics
"""
import os
import logging

from alchemy.testcase_results import Testcase_Result
import alchemy.database_manager as dbm
from alchemy.students import Students

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
        :return: the average cpu time
        """
        return self.average_euclidean_runtime_competition(run)


    @staticmethod
    def average_euclidean_runtime_competition(run):
        """
        computes the average euclidean cpu time for the competition
        with regard to the extra testcases
        (optional metric)
        :param run: the respective run
        :return: the average cpu time
        """
        return Testcase_Result.get_avg_runtime_performace(run)

    #@staticmethod
    #def geometric_mean_space(submission):
        """
        computes the geometric mean of
        all maximum resident set sizes
        for all of the good input testcases
        :param submission: the respective submission
        :return: the geometric mean of the maximum resident set sizes
        """
    #    good_test_cases = submission.tests_good_input
    #    n = len(good_test_cases) + 1
    #    geom_mean = 1.0
    #    for i in good_test_cases:
 #   #        current_component = i.mrss ** (1 / float(n))
  #          geom_mean *= current_component
#
   #     return geom_mean



    def get_performance(self, run):
        """
        Computes a complete performance dictionary
        :param submission: the respective submission
        :return: the performance dictionary
        """
        
        time=Testcase_Result.get_avg_runtime_performance(run)
        space=Testcase_Result.get_avg_space_performance(run)
        return performance_stats[time,space]


    def evaluate(self, studentlog):

        """
        evaluates all students if they had passed
        with regard to their performance
        and prints the results into a file an to console
        :param studentlog: studentlog with all students
        :return:None
        """
        performances = []
        students = Students.get_students_passed()
        for student in students:
            for submission in student.submissions:
                for run in submission.runs:
                    if run.passed:
                        p=self.get_performance(run)
                        performance.append(p)
        
        #TODO Continue                
        raise Error("not implemented")

        performances = []
        for i in students:
            if (p := database_manager.get_performance(i)) is not None:
                

        key_list = list(performances[0].keys())

        try:
            os.unlink("performances.txt")
        except FileNotFoundError:
            pass

        row_format = ' | '.join(['{name}'] + ['{{{}:.2f}}'.format(col)
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

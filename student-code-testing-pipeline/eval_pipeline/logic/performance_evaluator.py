"""
Implements all functionality needed to run performance statistics for student submissions.
"""
import os
import logging
from database.testcase_results import TestcaseResult
import database.database_manager as dbm
from database.students import Student
from database.runs import Run
from util.absolute_path_resolver import resolve_absolute_path
from util.config_reader import ConfigReader
from util.htable import table_format

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


class PerformanceEvaluator:
    """
    Implements a Performance evaluator which provides all functionality to run performance evaluation and statistics.
    """

    def __init__(self):
        """
        Initialises PerformanceEvaluator using a config file.
        """
        config_path=resolve_absolute_path(
            "/resources/config_performance_evaluator.config")
        self.configuration=ConfigReader() \
            .read_file(os.path.abspath(config_path))

    def evaluate_performance(self, submission, run):
        """
        Checks whether a submission is performant based on a single run.
        Parameters:
            submission (Submission object): the respective submission

        Returns; Nothing
        """
        performant=True
        metric=TestcaseResult.get_avg_runtime(run)
        if metric>float(self.configuration["THRESHOLD"]):
            performant=False
        if submission.is_fast is False or submission.is_fast is None:
            submission.is_fast=performant
            dbm.session.commit()

    def evaluate(self):
        """
        Evaluates all students if they had passed with regard to their performance.
        Uses a set of testcases specified in the configuration file under "PERFORMANCE_TESTCASES_TIME".
        Prints a table of results into a file to the console.
        Will also create a file named performance.html containing the results.
        Parameters: None
        Returns: Nothing
        """
        key_list=self.configuration["PERFORMANCE_TESTCASES_TIME"]
        performances=list()
        students=Student.get_students_passed()
        for student in students:
            fastest=Run.get_fastest_run_for_student(student.name, key_list)
            if fastest is not None:
                run, submission, time, space=fastest

                result={'name': student.name, 'mrss': space}
                for key in key_list:
                    testcase_result=TestcaseResult.get_testcase_result_by_run_and_testcase(run.id, testcase_name=key)
                    if testcase_result is not None:
                        result[key]=testcase_result.tictoc
                    else:
                        result[key]=""
                performances.append(result)

        try:
            os.unlink("performances.txt")
        except FileNotFoundError:
            pass
        
        if performances == []:
            logging.info(f'There are now performances that are both passed and fast. Therefore no table  can be created.')
            exit(0)

        row_format=' | '.join(['{name}']+['{{{}:.3f}}'.format(col)
                                          for col in
                                          self.configuration[
                                              "PERFORMANCE_TESTCASES_TIME"
                                          ]]
                              +['{mrss:.0f}'])
        key_list.append("mrss")

        filename="performances.html"
        try:
            os.remove(filename)
        except:
            pass

        for i in range(0, len(key_list)):
            print(f"\nSorted by {key_list[i]}:\n")
            print(table_format(
                row_format,
                sorted(performances, key=lambda k: float(k[key_list[i]])),
                titles='auto'))

            with open(filename, "a+") as file:
                print(f"\nSorted by {key_list[i]}:\n", file=file)
                print(table_format(
                    row_format,
                    sorted(performances,
                           key=lambda k: float(k[key_list[i]])),
                    titles='auto',
                    html=True,
                    highlight=key_list[i]),
                    file=file)

        ranking=list()
        for el in performances:
            sum=0
            for key in key_list[:-1]:
                sum+=el[key]
            ranking.append([el['name'], sum])

        sorting=sorted(ranking, key=lambda k: k[1])
        mean_ranking=list()
        for nr, s in enumerate(sorting):
            name=s[0]
            sum_rank=0
            for i in range(0, len(key_list)):
                sort_perform=sorted(performances, key=lambda k: float(k[key_list[i]]))
                for rank, dict in enumerate(sort_perform):
                    if dict['name']==name:
                        sum_rank+=rank
                        break
            mean=sum_rank/len(key_list)
            mean_ranking.append([name, mean])

        sorting_ranking=sorted(mean_ranking, key=lambda k: float(k[1]))
        for nr, s in enumerate(sorting_ranking):
            print(f"{nr}. {s}")

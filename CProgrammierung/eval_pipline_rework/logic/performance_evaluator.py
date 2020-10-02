"""
Implements all functionality needed to run
performance statistics
"""
import os

from util.absolute_path_resolver import resolve_absolute_path
from util.config_reader import ConfigReader
from util.htable import table_format


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

    def evaluate_performance(self, submission):
        """
        checks whether a submission is performant
        :param submission: the respective submission
        :return: None
        """
        performant = True
        metric = self.average_euclidean_cpu_time(submission)
        if metric > self.configuration["THRESHOLD"]:
            performant = False

        submission.performant = performant
        submission.performant = True

    def evaluate_competition(self, submission):
        """
        evaluates a submission for the competition
        (a optional metric)
        :param submission: the respective submission
        :return: the average cpu time
        """
        return self.average_euclidean_cpu_time_competition(submission)

    @staticmethod
    def average_euclidean_cpu_time(submission):
        """
        computes the average euclidean cpu time
        (optional metric)
        :param submission: the respective submission
        :return: the average cpu time
        """
        good_test_cases = submission.tests_good_input
        bad_test_cases = submission.tests_bad_input
        dist = 0.0
        for i in good_test_cases:
            dist = dist + i.cpu_time
        for i in bad_test_cases:
            dist = dist + i.cpu_time

        dist = dist / (len(good_test_cases) + len(bad_test_cases))
        return dist

    @staticmethod
    def average_euclidean_cpu_time_competition(submission):
        """
        computes the average euclidean cpu time for the competition
        with regard to the extra testcases
        (optional metric)
        :param submission: the respective submission
        :return: the average cpu time
        """
        extra_test_cases = submission.tests_extra_input
        if len(extra_test_cases) == 0:
            return float('nan')
        dist = 0.0
        for i in extra_test_cases:
            dist = dist + i.cpu_time

        dist = dist / (len(extra_test_cases))
        return dist

    @staticmethod
    def geometric_mean_space(submission):
        """
        computes the geometric mean of
        all maximum resident set sizes
        for all of the good input testcases
        :param submission: the respective submission
        :return: the geometric mean of the maximum resident set sizes
        """
        good_test_cases = submission.tests_good_input
        n = len(good_test_cases) + 1
        geom_mean = 1.0
        for i in good_test_cases:
            current_component = i.mrss ** (1 / float(n))
            geom_mean *= current_component

        return geom_mean

    def get_time_performance(self, submission):
        """
        retrieves a dictionary of all needed cpu time
        for given testcases
        :param submission: the respective submission
        :return: A dictionary of testcase ids to needed cpu time
        """
        testcases = submission.tests_good_input
        testcases.extend(submission.tests_extra_input)
        result = {}
        for i in testcases:
            if i.short_id in self.configuration["PERFORMANCE_TEST_CASES_TIME"]:
                result.update({i.short_id: i.cpu_time})
        return result

    def get_space_performance(self, submission):
        """
        calculates the needed space of a submission
        :param submission: the respective submission
        :return: dictionary mrss to geometric mean
        """
        return {"mrss": self.geometric_mean_space(submission)}

    def get_performance(self, submission):
        """
        Computes a complete performance dictionary
        :param submission: the respective submission
        :return: the performance dictionary
        """
        performance_stats = {}
        performance_stats.update(self.get_time_performance(submission))
        performance_stats.update(self.get_space_performance(submission))
        return performance_stats

    def insert_performance(self, database_manager, submission):
        """
        inserts a performance into a database
        :param database_manager: the respective database manager
        :param submission: the respective submission
        :return: None
        """
        result = self.get_performance(submission)
        student = database_manager.get_student_by_key(submission.student_key)
        database_manager.insert_performance(student, result)

    def evaluate(self, studentlog, database_manager):
        """
        evaluates all students if they had passed
        with regard to their performance
        and prints the results into a file an to console
        :param studentlog: studentlog with all students
        :param database_manager: a database representation
        :return:None
        """
        students = [i for i in studentlog if i.passed]
        for i in students:
            for j in i.submissions:
                if j.passed:
                    self.insert_performance(database_manager, j)

        performances = []
        for i in students:
            if (p := database_manager.get_performance(i)) is not None:
                performances.append(p)

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

class PerformanceEvaluator:
    def __init__(self):
        pass

    def evaluate_performance(self, submission):

        metric = self.average_euclidean_cpu_time(submission)
        submission.performant = True

    def evaluate_competition(self, submission):
        return self.average_euclidean_cpu_time_competition(submission)

    @staticmethod
    def average_euclidean_cpu_time(submission):
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
        extra_test_cases = submission.tests_extra_input
        dist = 0.0
        for i in extra_test_cases:
            dist = dist + i.cpu_time

        dist = dist / (len(extra_test_cases))
        return dist

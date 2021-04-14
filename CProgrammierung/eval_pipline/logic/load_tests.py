import os
import traceback
import logging
from signal import SIGABRT, SIGTERM, SIGSEGV, SIGILL, signal, SIGINT

from moodel.database_integrator import DatabaseIntegrator
from moodel.moodle_reporter import MoodleReporter
from moodel.moodle_submission_fetcher import MoodleSubmissionFetcher
from logic.performance_evaluator import PerformanceEvaluator
from logic.result_generator import ResultGenerator
from logic.test_case_executor import TestCaseExecutor
from logic.abtestat_functions import Abtestat_Functions
from util.argument_extractor import ArgumentExtractor
from util.lockfile import LockFile
from util.playground import Playground
from database.database_manager import DatabaseManager 
from logic.mark_manual import marke_passed_manually
from logic.execute_single import execute_singel_testcase

LOCK_FILE_PATH = '/run/lock/check.lock'
FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)





def load_tests(configuration):
    """
    Loads the in the config file specified testcases for good bad and extra
    :return: dictionary of list test_case
    test_case_type -> [test_cases]
    """
    test_cases = {}
    extensions = {"BAD": configuration["TESTS_BAD_EXTENSION"],
                  "GOOD": configuration["TESTS_GOOD_EXTENSION"],
                  "EXTRA": configuration["TESTS_EXTRA_EXTENSION"]} #Testcase types in this directory: Bad_OR_OUTPUT, PERFORMANCE
    test_case_id = 0
    json_descriptions = {}
    
    for key in extensions:
        
        test_case_input = []
        path_prefix = os.path.join(resolve_absolute_path(configuration["TESTS_BASE_DIR"]), extensions[key])
        for root, _, files in os.walk(path_prefix,topdown=False):
            for name in files:
                
                if name.endswith(".stdin"):
                    short_id = name.replace(".stdin", "")
                    path=os.path.join(root, name).replace(".stdin", "")
                    #logging.debug(short_id)
                    
                    json_file=(root+"/"+name).replace(".stdin", ".json")
                    if(os.path.exists(json_file)):
                        with open(json_file) as description_file:
                            json_rep=json.load(description_file)
                            description = json_rep["short_desc"]
                            hint = json_rep["hint"]
                            valgrind=json_rep["valgrind"]
                            #logging.debug(root)
                            type=json_rep["type"]
                            
                            Testcase.create_or_update(path, short_id, description, hint, type, valgrind=valgrind)
                            #logging.debug(testcase)
                    else: 
                        description= short_id
                        hint = f"bei {short_id}"
                        type="UNSPEZIFIED"
                        if extensions["GOOD"] in root: type="GOOD"
                        elif extensions["BAD"] in root: type="BAD"
                        #elif extensions["EXTRA"] in root: type="EXTRA"
                        #logging.debug(root)
                        if type=="UNSPEZIFIED":
                            logging.warning(f"Test at {path} was ignored because no type can be assinged. Either place the Testcase in the folders for good or bad testcases or create an .json file that specifies the type.")
                        else:
                            Testcase.create_or_update(path, short_id, description, hint, type)
                                    
                                    

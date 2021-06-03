"""
This module manages all test case execution and evaluation
"""
import json
import os
import logging

from util.absolute_path_resolver import resolve_absolute_path
from database.testcases import Testcase


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
                            try:
                                type=json_rep["type"]
                            except KeyError:
                                 if extensions["GOOD"] in root: type="GOOD"
                                 elif extensions["BAD"] in root: type="BAD" 
                            rlimit=json_rep["rlimit"]
                            if "MB" in rlimit:  
                                rlimit=int(float(rlimit[:-2])*1000000)
                        
                            elif "M" in rlimit: 
                                rlimit=int(float(rlimit[:-1])*1000000)
                            else:
                                logging.error(f"Unknown unit in file {name} for rlimit. Using 1MB.")
                                rlimit=1000000
                            #print(f"rlimit {rlimit}")
                            Testcase.create_or_update(path, short_id, description, hint, type, valgrind=valgrind,rlimit=rlimit)
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
                                    
                                    

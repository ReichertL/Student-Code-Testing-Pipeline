"""
This module loads testcases and stores them in the database.
"""
import json
import os
import logging

from util.absolute_path_resolver import resolve_absolute_path
from database.testcases import Testcase

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


def load_tests(configuration):
    """
    Loads the in the config file specified testcases for good, bad and extra.
    Testcases can be given the type UNSPECIFIED here if the type could not be derived from the folder structure
    or no corresponding ".json" file containing a description of the testcase was found.

    Parameters:
        configuration (dict): configuration '/resources/config_testcase_executor.config' as dict
        containing the keys TESTS_BAD_EXTENSION, TESTS_GOOD_EXTENSION, TESTS_EXTRA_EXTENSION, TESTS_BASE_DIR
        and corresponding paths to the folders.
        
    Returns:
        Nothing.
    
    """
    testcases={}
    extensions={"BAD": configuration["TESTS_BAD_EXTENSION"],
                "GOOD": configuration["TESTS_GOOD_EXTENSION"],
                "EXTRA": configuration[
                    "TESTS_EXTRA_EXTENSION"]}  # Testcase types in this directory: BAD_OR_OUTPUT, PERFORMANCE

    for key in extensions:
        path_prefix=os.path.join(resolve_absolute_path(configuration["TESTS_BASE_DIR"]), extensions[key])
        for root, _, files in os.walk(path_prefix, topdown=False):
            for name in files:

                if name.endswith(".stdin"):
                    short_id=name.replace(".stdin", "")
                    path=os.path.join(root, name).replace(".stdin", "")

                    json_file=(root+"/"+name).replace(".stdin", ".json")
                    if os.path.exists(json_file):
                        with open(json_file) as description_file:
                            json_rep=json.load(description_file)
                            description=json_rep["short_desc"]
                            hint=json_rep["hint"]
                            valgrind=json_rep["valgrind"]
                            try:
                                type=json_rep["type"]
                            except KeyError:
                                if extensions["GOOD"] in root:
                                    type="GOOD"
                                elif extensions["BAD"] in root:
                                    type="BAD"
                            rlimit_json=json_rep["rlimit"]
                            if "MB" in rlimit_json:
                                rlimit=int(float(rlimit_json[:-2])*1000000)

                            elif "M" in rlimit_json:
                                rlimit=int(float(rlimit_json[:-1])*1000000)
                            else:
                                logging.error(f"Unknown unit in file {name} for rlimit. Using 1MB.")
                                rlimit=1000000
                            Testcase.create_or_update(path, short_id, description, hint, type, valgrind=valgrind,
                                                      rlimit=rlimit)
                    else:
                        description=short_id
                        hint=f"bei {short_id}"
                        testcase_type="UNSPECIFIED"
                        if extensions["GOOD"] in root:
                            testcase_type="GOOD"
                        elif extensions["BAD"] in root:
                            testcase_type="BAD"
                        if testcase_type=="UNSPECIFIED":
                            logging.warning(
                                f"Test at {path} was ignored because no type can be assinged. "
                                f"Either place the Testcase in the folders for good or bad testcases"
                                f" or create an .json file that specifies the type.")
                        else:
                            Testcase.create_or_update(path, short_id, description, hint, testcase_type)

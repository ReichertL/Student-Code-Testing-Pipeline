Reworked python eval pipeline for evaluating c-programming project submissions.
Thanks to __init.py__ and __main.py__
it can be called by executing python3 /path/to/eval_pipeline/
There needs to be a resource directory inside the eval_pipline directory
which contains config_database_integrator.config, config_database_manager.config,
config_submission_fetcher.config and config_test_case_executor.config.
These files are used to set relevant constants.
There are example .config files included that need to be adjusted appropriately.

Commandline arguments currently implemented:
    -a testing all submissions
    -r rerun tested submissions
    -f fetches students and submissions from a given base dir
    -v prints extended information

Implemented features:
    Integrating an existing submission dir into a sql-lite database
    Running given test cases for all submissions in the database
    Evaluate the results
    marking students and submissions as passed (current bug, valgrind not taken into account)

Roadmap
    evaluating memory footprint for passing
    automate moodle submission fetching
    evaluate runtime statistics
    automate feedback sending
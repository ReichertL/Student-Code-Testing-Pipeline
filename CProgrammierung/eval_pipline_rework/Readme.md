# Reworked python eval pipeline for evaluating c-programming project submissions. #


Thanks to `__init__.py` and `__main__.py`
it can be called by executing

```
python3 /path/to/eval_pipeline/
```

or

```
/path/to/eval_pipeline/__main__.py
```

## Installation and Setup


There needs to be a resource directory inside the `eval_pipline directory`
which contains:

  - `config_database_integrator.config`
  - `config_database_manager.config`
  - `config_submission_fetcher.config`
  - `config_test_case_executor.config`
  - `config_performance_evaluator.config`

These files are used to set relevant constants.
There are example `.config` files included in the `resource.templates` directory that need to be adjusted appropriately.

For convenience, put a symbolic link in `/usr/bin`:
```
sudo ln -s /path/to/eval_pipeline/__main__.py /usr/bin/check
```

If you want to use the automatic email functionality you might want to define a `mail_templates` directory,
where you define all relevant error messages that can be part of an email to a student.
It's worth to note, that these template massages can contain placeholder tokens,
which can be replaced during runtime. These tokens should be follow the format `$placeholder_token$`.  
 

## Current state of the rework


###Commandline arguments currently implemented:

    -a testing all submissions
    -r rerun tested submissions, also requests resending of emails
    -f fetches students and submissions from moodle and saves them local
       and generates a respective database entry
    -v prints extended information
    -g generating full .csv grading files for uploading at moodle 
    -s prints short statistics for all submissions and all students
    -d prints full information for a/some student/s submission given
       if more than one submission is found the user is asked 
    
    -A marks a student or a list of students as "abtestat done" if the student hasn't passed 
       all test the user will be asked
    -R reverts marking a student or a list of students as "abtestat done" 
       the user will also be ask whether to unset passed test cases


###Implemented features:

  - Integrating an existing submission dir into a sql-lite database
  - Running given test cases for all submissions in the database
  - Evaluate the results
  - marking students and submissions as passed (current bug, valgrind not taken into account)
  - integrated submission fetching from moodle course
  - integrated automatic feedback 

##Future Development

  - evaluating memory footprint for passing
  - evaluate runtime statistics
  - integrate 3rd party orm like SqlAlchemy (in progress)



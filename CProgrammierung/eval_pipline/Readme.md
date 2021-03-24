# Reworked python eval pipeline for evaluating c-programming project submissions

This python script is intended to automatically fetch submissions from a moodle page, compile these submissions for each
student and evaluate the correctness along with the performance. 
Further it is able to persist relevant information, send feedback e-mails and generate relevant grading for moodle via 
csv and also via the moodle grading api.   

## Content
1. [Installation](#installation)
2. [Usage](#usage)
3. [Current State of the Eval Pipeline](#current-state-of-the-eval-pipline)
4. [Future Development](#future-development)


## 1. Installation
### 1.1 Packages
Install Docker and Valgrind:

  - `sudo apt install docker.io`
  - `sudo apt install valgrind`

Ensure that python3.8 is installed if not use the following command (works on Ubuntu 18.04):

`$ sudo apt-get install python3.8 python3.8-dev python3.8-distutils python3.8-venv`

Install required packet bs4 for python3.8 by using:

  - `python3.8 -m pip install bs4`
  - `python3.8 -m pip install sqlalchemy`




### 1.2 Docker

Build Docker File:
  - `./dockerfiles/build.sh`

### 1.3 Resources, Config Files and Templates

There needs to be a resource directory inside the `eval_pipline directory`
which contains:

  - `config_database_integrator.config`
  - `config_database_manager.config`
  - `config_submission_fetcher.config`
  - `config_test_case_executor.config`
  - `config_performance_evaluator.config`

These files are used to set relevant constants.
There are example `.config` files included in the `resource.templates` directory that need to be adjusted appropriately.

If you want to use the automatic email functionality you might want to define a `mail_templates` directory,
where you define all relevant error messages that can be part of an email to a student.
It's worth to note, that these template massages can contain placeholder tokens,
which can be replaced during runtime. These tokens should be follow the format `$placeholder_token$`. 


### 1.4 Moodel Course
Set up a Moodel Course with an excercise where students can submit a `.c` file. 
Set the maximal possible grade for this excersie to 2:
The grading for the C project is as follows:

   - 0=not passed
   - 1=submission passed
   - 2= abtestat passed

Retrieve the course ID, submission ID and ID of the account that sould be used by the pipline for logging  into moodel.
This can be done by opening the respective page in the web browser an copying the Id from the url. 
With these values update the entries in `C Programmierprojekt/eval_pipline_rework/resources` the file named `config_submission_fetcher.config`.

### 1.5 Shortcut
For convenience, put a symbolic link in `/usr/bin` so that the pipline can be called by simply running `check [args]` in the terminal:
```
sudo ln -s /path/to/eval_pipeline/__main__.py /usr/bin/check
```

## Usage
Thanks to `__init__.py` and `__main__.py`
it can be called by executing:

`/path/to/eval_pipeline/__main__.py [args]`

(For some reason this does not work when you are already in the directory `eval_pipeline`)
Relevant switches and flags accessible with `check -h`

For convenience it is possible to create an alias or symbolic link(see [Installation]).
It can then be called by:

`check [args]`

### Usefull Commands

During the semester:

* `check -f` : Fetches all (new) submission but does not execute them
* `check -fa`: Fetches new submissions and checks them for correctness (will not notify student)
* `check -m` : Sends mail to all students that have not yet received a mail for their last submission (semi-automatic, requires user interaction)
* `check -c "Firstname Lastname"` : Will run a specific submission (which is selectable) for a specific student. If student name does not match completly, a student will be suggested.
* `check -t "Firstname Lastname"` : Run a single (selectable) testcase for the named student.
* `check -tOV "Firstname Lastname"` : Run single testcase for student but also print output and Valgrind result. 
* `check -d "Firstname Lastname"`: Get information about the last submissions of a single student.
* `check -D "Firstname Lastname"` : Manually mark a submission as correct. Student will be automatically marked as passed. The database records manual change in a corresponding flag. This can be done if there are errors with the pipline and student code was successfully run on gruenau.

For Abtestate:
* `check -db "Firstname Lastname"`: Get information about the best submissions of a single student.
* `check -s` : List for all students that have submitted a solution if they have passed. Useful when reevaluating the bar for passing.
* `check -F` : Reruns all submission while ignoring the compiler warnings (and maybe some other stuff too). 
* `check -uF` : check all unpassed students (and all their submissions) while lowering the bar for passing.
* `check -A "Firstname Lastname"` : Record a successful Abtestat for this student. Marks the student as passed if not passed in the database.
* `check -R "Firstname Lastname"` : Revert the desicion on an Abtestat. Allows to remove the passed status of a student.
* `check -g`: Generates .csv files of students that have passed for the Prüfungsbüro.  


## Current State of the Eval Pipeline
This section describes the current state of the eval pipeline. 
We start with the currently usable switches and their behavior, [here](#stable-commandline-arguments). 
Followed by a description of the [current structure](#implemented-structure) and finish with a short summary of 
the [current features](#implemented-features).   


### Implemented Structure:
The image below represents the currently implemented structure of the evaluation pipeline. 
![current structure](Database_Schema.svg)


### Implemented Features:  
  - Fetching submissions from moodle or a local dir 
  - Persist student data and submission information in a sqlite database 
  - Run a specific set of Testcases, consisting of input and output, for all submissions 
  - Evaluate the results with regards to correctness and runtime  
  - Marking students as passed, and also mark whether they passed an "abtestat"
  - Send evaluation feedback to the students after running tests
  - evaluate performance (time and space) to evaluate possible competitions
  - dump relevant grading lists via csv and Moodle Grader API
  - Guessing a students name based on input
  

## Future Development
In this section we'll describe planned future reworks and structural improvements for future work.


### Planned Features

- separate operations with flag for students single, list, all and for submissions not_passed, latest, all 
- rework format of -s/--stats 

### Planned Integration 

- pair-wise similarity analysis with j-plag
- test coverage for eval pipeline



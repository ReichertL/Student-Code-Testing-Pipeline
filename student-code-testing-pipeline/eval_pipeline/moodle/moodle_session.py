"""
This module deals with logging into moodle with credentials provided in the configuration file.
It also maintains the session, instead of logging in every time.
"""
import getpass
import itertools
import json
import os
import re
import subprocess
import sys
import time
from pwd import getpwnam
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import urllib.parse
import logging
from math import floor
from util.absolute_path_resolver import resolve_absolute_path
from database.students import Student
import database.database_manager as dbm

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)


AJAX_HEADERS = {
    'X-Requested-With': 'XMLHttpRequest',
    'Pragma': 'no-cache',
    'Content-Type': 'application/json; charset=UTF-8',
    'Cache-Control': 'no-cache',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
}

DEFAULT_SESSION_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;'
              'q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Host': '',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:74.0) '
                  'Gecko/20100101 Firefox/74.0',
}


class MoodleAjaxError(Exception):
    """Unknown json reply from the Moodle AJAX API."""


class MoodleScrapeError(Exception):
    """Unexpected document structure of scraped HTML document."""


class MoodleSession:
    """
    This class handles maintaining moodle sessions.
    """
    def __init__(self, username, session_state, configuration, interactive=True):
        """
        Here the MoodleSession class is initialized.
        Parameters:
            username (string): username used for logging in
            session_state (dict): contains information about the status of the session
            configuration
            interactive (Boolean): . Optional. Default True.
        """
        self.configuration = configuration
        self.full_name = '<unknown>'
        self.userid = ''
        self.session_state = {
            'sesskey': '',
            'logged_in': False,
            'cookie': ''}
        self._last_request = None
        self.session = requests.Session()
        self.domain = configuration["MOODLE_DOMAIN"]
        DEFAULT_SESSION_HEADERS['Host'] = self.domain
        self.proto='https://'
       
        docker=os.environ['DOCKER_ENV']
        if docker == "TRUE":
            self.proto='http://'

        self.session.headers.update(DEFAULT_SESSION_HEADERS)
        self.read_users_cached()
        self.username = username
        self.session_state = session_state
        #logging.info(session_state)
        #logging.info(session_state.get('logged_in'))
        if session_state and session_state.get('logged_in') is True:
            #logging.info("si")
            self.session.cookies.set('MoodleSession', session_state['cookie'],
                                     path='/', domain=self.domain)
            self.query_logged_in()
        if interactive:
            if not session_state or not self.session_state['logged_in']:
                self.login()
        self._grader_contextid = None
        self._grader_assignmentid = None
        
            

    def read_users_cached(self):
        """Read in the users list found in a cache file 'teilnehmer.json' in
        the current working directory."""
        self.teilnehmer = Student.get_students_all()

    @property
    def moodle_base_url(self):
        """
        Creates a base url string.
        Parameters: None
        Returns:
            URL string
        """
        return self.proto + self.domain

    def update_students(self):
        """
        Fetch moodle course user index and save names and moodle id to the database.
        Uses the MOODLE_COURSE_ID from the configuration files.
        Parameters: None
        Returns: Nothing
        """
        course_id = self.configuration["MOODLE_IDS"]["MOODLE_COURSE_ID"]
        re_students = re.compile(
            r'<a href="{}/user/view.php\?id=(\d+)&amp;course=(\d+)" class="d-inline-block aabtn">'
            r'<img src="[^"]*"\s+class="[^"]*"[^>]*>([^<]+)</a>'.format(
                re.escape(self.moodle_base_url)))
        res = {}
        url = self.moodle_base_url + '/user/index.php'
        r = self.session.get(url, params={'id': course_id, 'perpage': '5000'})
        self._last_request = r
        for line in r.text.splitlines():
            mo = re_students.search(line)
            if mo:
                id_, course_id, name = mo.group(1, 2, 3)
                res[name] = id_

        logging.info('Found {} Students.'.format(len(res)))

        if res:
            for i in res:
                Student.get_or_insert(i, res[i])
        dbm.session.commit()

    def logged_in(self):
        """
        Just a shortcut to the session state.
        To re-verify the true logged-in-state, use `query_logged_in` instead.
        Parameters: None
        Returns: Boolean
        """
        return (self.session_state['logged_in']
                and len(self.userid) > 0)

    def query_logged_in(self):
        """
        Try to fetch and scrape dashboard. We use this to find out,
        whether we are currently logged in.
        Parameters: None
        Returns: Boolean
        """
        r = self.session.get(self.moodle_base_url + '/my/')
        self.scrape_dashboard(r)
        self._last_request = r
        return self.logged_in()

    def login(self):
        """
        Login into Moodle with a password and username set in the configuration files.
        This queries the password but does not store it.

        !!!  USE AT OWN RISK  !!!

        Even though the password is not written to disk explicitly, who knows
        where it is cached to by python.
        
        For this to work, a login token is required.
        The function gets the logintoken from the Moodle login form.
        If login fails, the pipeline terminates with an error code.


        Parameters: None
        Returns: Nothing
        """

        login_url = self.proto + self.domain + '/login/index.php'

        r = self.session.get(login_url)
        soup = BeautifulSoup(r.text, 'html.parser')
        hidden_tags = soup.find_all("input", type="hidden")
        for tag in hidden_tags:
            if tag['name']=="logintoken":
                logintoken=tag['value']
                logging.info(tag['value'])
                break
                
        d = {'username': self.username,
             'password': self.configuration
                 .get("MOODLE_PASSWORDS", {})
                 .get(self.username),
            'logintoken': logintoken
                 }
        if d['password'] is None:
            d['password'] = getpass.getpass(
                f'[logging in as {self.username}] Password: ')
        logging.info(f'INFO: logging in as "{self.username}" ')

        self._last_request = self.session.post(login_url, data=d)
        self.session_state['cookie'] = self.session.cookies['MoodleSession']
        if self.query_logged_in():
            logging.info(f'OK, your full name is "{self.full_name:s}"')
        else:
            logging.error(f'Login FAILED. Post data {d}. Post URL {login_url}.')
            exit(1)

    @staticmethod
    def dump_dashboard(r):
        """
        Dump r.text to /tmp/dashboard%03d.html
        For debugging only.
        Parameters: TODO
        returns; Nothing
        """
        for i in itertools.count():
            html_dump_path = f'/tmp/dashboard{i:03d}.html'
            if not os.path.exists(html_dump_path):
                break
        print(f'MoodleSession.scrape_dashboard() -> {html_dump_path}')
        with open(html_dump_path, 'w') as f:
            f.write(r.text)

    def scrape_dashboard(self, r):
        """
        Scrape the Moodle dashboard to retrieve full name, user id and session key.
        Parameters:

        Returns: Nothing
        """
        d = BeautifulSoup(r.text, 'html.parser')
        try:
            # dashboard is only loaded if we are logged in
            self.session_state['logged_in'] = \
                d.find_all('title')[0].text == 'Dashboard'
        except IndexError:
            self.session_state['logged_in'] = False
        try:
            # <div class='logininfo' .../> contains all data we need
            div = d.find_all('div', attrs={'class': 'logininfo'})
            if len(div) != 1:
                raise MoodleScrapeError(
                    'cannot find <div class=\'logininfo\' .../>')
            # extract the full name
            try:
                self.full_name = div[0].find_all('a')[0].text
            except IndexError:
                logging.warning("Could not find Full Name")
            # extract the moodle user id
            url = div[0].find_all('a')[0]['href']
            if (mo := re.match(r'(.*?=)(\d+)', url)) is not None:
                if mo.group(1) != self.moodle_base_url + '/user/profile.php?id=':
                    raise MoodleScrapeError(
                        'cannot find link .../user/profile.php?id=...')
                self.userid = mo.group(2)
            else:
                raise MoodleScrapeError(
                    'cannot find link .../user/profile.php?id=...')
            # extract the sesskey
            url = div[0].find_all('a')[1]['href']
            if (mo := re.match(r'(.*?=)(\w+)', url)) is not None:
                if mo.group(1) != self.moodle_base_url \
                        + '/login/logout.php?sesskey=':
                    raise MoodleScrapeError(
                        'cannot find link .../login/logout.php?sesskey=...')
                self.session_state['sesskey'] = mo.group(2)
            else:
                raise MoodleScrapeError(
                    'cannot find link .../login/logout.php?sesskey=...')
        except (IndexError, MoodleScrapeError) as e:
            sys.stderr.write('ERROR: unexpected error in dashboard parsing')
            # FixMe where does this come from?
            # std.esterr.write(f'-> {e:s}')
            self.dump_dashboard(r)
            self.session_state['logged_in'] = False
        self.dump_state()

    def fetch_grader_contextid_assignmentid(self):
        """
        Fetches information relevant for automating grading of students via Moodle.
        Sets _grader_contextid and _grader_assignmentid for the current object.
        Parameters:None
        Returns: Nothing.
        """
        r = self.session.get(
            self.moodle_base_url + '/mod/assign/view.php',
            params={'id': self.configuration['MOODLE_IDS']['MOODLE_SUBMISSION_ID'],
                    'action': 'grader'})
        d = BeautifulSoup(r.text, 'html.parser')
        divs = d.find_all('div', attrs={'data-region': 'grade'})
        if len(divs):
            div = divs[0]
            self._grader_contextid = div.attrs['data-contextid']
            self._grader_assignmentid = div.attrs['data-assignmentid']

    @property
    def grader_contextid(self):
        if self._grader_contextid is None:
            self.fetch_grader_contextid_assignmentid()
        return self._grader_contextid

    @property
    def grader_assignmentid(self):
        if self._grader_assignmentid is None:
            self.fetch_grader_contextid_assignmentid()
        return self._grader_assignmentid

    def dump_state(self):
        """
        Dump the current session's cookie and key to disk using the path from  the corresponding config file.
        Parameters: None
        Returns: Nothing
        """
        session_data_path = resolve_absolute_path(self.configuration["SESSION_DATA_PATH"])

        if not self.username:
            return
        try:
            with open(session_data_path) as f:
                all_sessions = json.load(f)
        except OSError:
            all_sessions = {}
        if self.session_state['logged_in']:
            self.session_state['cookie'] = \
                self.session.cookies['MoodleSession']
        all_sessions[self.username] = self.session_state
        all_sessions[self.username]['last_access'] = time.time()
        with open(session_data_path, 'w+') as f:
            json.dump(all_sessions, f, indent=2)

    def download_all_submissions(self, id_: str = None) -> str:
        """
        Download all submission of a Moodle exercise (usually a zip).
        Parameters:
            id_ (string): The id of the  programming exercise

        Returns:
            Local path of the downloaded file or None, if download failed.
        """
        if id_ is None:
            id_ = self.configuration["MOODLE_IDS"]["MOODLE_SUBMISSION_ID"]
        dest = self.configuration["SUBMISSION_NEW_ZIP"]
        r = self.session.get(self.moodle_base_url + '/mod/assign/view.php',
                             params={'id': id_, 'action': 'downloadall'},
                             stream=True)
        self._last_request = r
        Path(dest).touch(exist_ok=True)
        if r.status_code == 200:
            with open(dest, 'bw') as f:
                for x in r.iter_content(4096):
                    f.write(x)
            return dest
        return None

    def open_conversation_in_ff(self, touserid):
        """
        Open the instant messages Moodle view in browser. For debugging.
        Parameters:
            touserid (string): id identifying the conversation in the url
        Returns: Nothing
        """
        cmd_line = [self.configuration["FIREFOX_PATH"],
                    self.get_conversation_url(touserid)]
        if os.path.exists(self.configuration["FIREFOX_PATH"]):
            subprocess.call(cmd_line)
        else:
            print("firefox '{}'".format(cmd_line[1]))

    def get_conversation_url(self, touserid):
        """
        Return the url of the instant message conversation view regarding
        a specific user.
        Parameters:
            touserid (string): id identifying the conversation in the url
        Returns:
            URL string to open a certain conversation without the domain name
        """
        return '{}/message/index.php?user={}&id={}'.format(
            self.moodle_base_url, self.userid, touserid)

    def send_instant_message(self, touserid, text):
        """
        Send an instant message `text` to the user `touserid`.
        Note that text is interpreted as HTML, so literal `<>&`s will need
        to be escaped.
        Parameters:
            touserid (string): id identifying the conversation in the url
            text (string): message text to send to the student
        Returns:
            If successful, the text actually sent.
            In case of failure, returns False.
        """
        try:
            logging.debug(f"touserid {touserid}")
            data = self._ajax_call(
                'core_message_send_instant_messages',
                {"messages": [{"touserid": int(touserid), "text": text}]},
                referer='/message/index.php')[0]
        except (MoodleAjaxError, IndexError):
            logging.error("MoodleAjaxError or IndexError")
            return False

        if data.get('msgid', -1) > -1:
            return data.get('text', False)
        
        if data.get('msgid', -1) == -1:
            error="Die Mitteilung ist länger als erlaubt."
            if data.get('errormessage')==error:
                logging.debug("Spliting Message and send in two parts.")
                
                half=floor(len(text)/2)
                success1=self.send_instant_message(touserid, text[:half])
                if success1 ==False:
                    logging.debug("Sending first part failed")
                    return False
                success2=self.send_instant_message(touserid, text[half-5:])
                if success2!=False:
                    return ("first message: "+success1+" second message:"+success2)
        logging.debug(data)
        return False

    def get_current_grading(self, userid, return_editor_itemid=False):
        """
        Get current grade of a student on Moodle.
        Parameters:
            userid (string or int): Moodle ID of student
            return_editor_itemid (Boolean): whether to return the editor itemid
        Returns:
            grade
            or
            grade and editor itemid
        """
        rsp = self._ajax_call(
            'core_get_fragment',
            {'component': 'mod_assign',
             'callback': 'gradingpanel',
             'contextid': self.grader_contextid,
             'args': [{'name': 'userid', 'value': int(userid)},
                      {'name': 'attemptnumber', 'value': -1},
                      {'name': 'jsonformdata', 'value': '""'}]})
        self.debugdata = rsp
        d = BeautifulSoup(rsp['html'], 'html.parser')
        grade_str = d.find_all('span', attrs={'class': 'currentgrade'})[0].\
            find('a').text.replace(',', '.')
        try:
            grade = float(grade_str)
        except ValueError:
            grade = None
        itemid = None
        if not return_editor_itemid:
            return grade
        elements = d.find_all(
            'input',
            attrs={'type': 'hidden',
                   'name': 'assignfeedbackcomments_editor[itemid]'})
        if len(elements) > 0:
            itemid = elements[0].attrs['value']
        return grade, itemid


    def update_grading(self, userid, grade, text='', sendstudentnotifications=False):
        """
        Updates the grade for a student on moodle for a programming exercise.
        The grade is only updated if it differs from the current grade.
        Parameters:
            userid (string or int): moodle ID of the student
            grade (int): new grade of student.
            text (string): Feedback to student. Optional, default is ''.
            sendstudentnotifications (Boolean): Whether to inform the student about their new grade via a Moodle notification.

        Returns:
            True, if the grade was updated
            False, if the new grade is the same as the old grade

        """
        old_grade, editor_itemid = self.get_current_grading(userid, True)
        if old_grade == grade:
            return False
        if text != '' and not text.startswith('<'):
            text = '<p>{}<br></p>'.format(text)
        self._ajax_call(
            'mod_assign_submit_grading_form',
            {'assignmentid': self.grader_assignmentid,
             'userid': int(userid),
             'jsonformdata': json.dumps(
                 '&'.join([
                     'id={}'.format(self.configuration['MOODLE_IDS']['MOODLE_SUBMISSION_ID']),
                     'rownum=0',
                     'useridlistid=',
                     'attemptnumber=-1',
                     'ajax=0',
                     'userid=0',
                     'sendstudentnotifications={}'.format(json.dumps(bool(sendstudentnotifications))),
                     'action=submitgrade',
                     'sesskey={}'.format(self.session_state['sesskey']),
                     '_qf__mod_assign_grade_form_{}=1'.format(userid),
                     'grade={}'.format(str(grade).replace('.', ',')),
                     'assignfeedbackcomments_editor%5Btext%5D={}'.format(urllib.parse.quote(text)),
                     'assignfeedbackcomments_editor%5Bformat%5D=1',
                     'assignfeedbackcomments_editor%5Bitemid%5D={}'.format(editor_itemid)
                 ])
             )
            }
        )
        return True

    def _ajax_call(self, methodname: str, args, referer=None):
        """
        Make AJAX call through sevice.php.
        Parameters:
            methodname (string): A sending method such as core_message_send_instant_messages
            args (dict): Arguments for the message data part.
            referer(string) : Additional part to append to the domain. e.g. "/messages/index.html" Optional, default is None.

        Usage:
            data = self._ajax_call(
            'core_message_send_instant_messages',
            {"messages": [{"touserid": int(touserid), "text": text}]},

        Returns:
            Data part of the AJAX response.
        """
        headers = dict(AJAX_HEADERS)
        if referer:
            headers.update({'Referer': self.proto+ self.domain + referer})
        data = [{"index": 0,
                 "methodname": methodname,
                 "args": args}]
        r = self.session.post(
            self.configuration["AJAX_URL"],
            params={'sesskey': self.session_state['sesskey'],
                    'info': methodname},
            data=json.dumps(data),
            headers=headers)
        self._last_request = r
        try:
            d = json.loads(r.text)[0]
            if d['error']:
                if d['exception']['errorcode'] == 'servicerequireslogin':
                    self.handle_logout()
                raise MoodleAjaxError()
        except (KeyError, IndexError):
            raise MoodleAjaxError()
        return d['data']

    def handle_logout(self):
        """
        Clear the session variable cache because we are not logged in.
        """
        self.session_state['logged_in'] = False
        self.session_state['cookie'] = ''
        self.session_state['sesskey'] = ''
        self.dump_state()

import getpass
import itertools
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import urllib.parse
import logging
from math import floor
FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)

from util.absolute_path_resolver import resolve_absolute_path
from database.students import Student





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
    """Unknown json reply from the moodle AJAX API."""


class MoodleScrapeError(Exception):
    """Unexpected document structure of scraped HTML document."""


class MoodleSession:
    def __init__(self, username, session_state, configuration, interactive=True):
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
        self.session.headers.update(DEFAULT_SESSION_HEADERS)
        self.read_users_cached()
        self.username = username
        self.session_state = session_state
        if session_state and session_state.get('logged_in'):
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
        return 'https://' + self.domain

    def update_teilnehmer(self):
        """Fetch moodle course user index and save names and user ids as json.

        course_id defaults to constants.MOODLE_COURSE_ID

        """
        course_id = self.configuration["MOODLE_IDS"]["MOODLE_COURSE_ID"]
        re_teilnehmer = re.compile(
            r'<a href="{}/user/view.php\?id=(\d+)&amp;course=(\d+)" class="d-inline-block aabtn">'
            r'<img src="[^"]*"\s+class="[^"]*"[^>]*>([^<]+)</a>'.format(
                re.escape(self.moodle_base_url)))
        res = {}
        url = self.moodle_base_url + '/user/index.php'
        r = self.session.get(url, params={'id': course_id, 'perpage': '5000'})
        self._last_request = r
        #f=open("out.txt", 'w+')
        #f.write(r.text)
        #f.close()
        for line in r.text.splitlines():
            mo = re_teilnehmer.search(line)
            if mo:
                id_, course_id, name = mo.group(1, 2, 3)
                res[name] = id_

        print('Found {} Teilnehmer.'.format(len(res)))

        # dump teilnehmer list as json
        if res:
            for i in res:
                Student.get_or_insert(i, res[i])
                #print(i)

        #else:
        #    with open('users.html', 'w') as f:
        #        f.write(r.text)

    def logged_in(self):
        """Just a shortcut to the session state.

        To re-verify the true logged-in-state, use `query_logged_in` instead.
        """
        return (self.session_state['logged_in']
                and len(self.userid) > 0)

    def query_logged_in(self):
        """Try to fetch and scrape dashboard. We use this to find out,
        whether we are currently logged in."""
        r = self.session.get(self.moodle_base_url + '/my/')
        self.scrape_dashboard(r)
        self._last_request = r
        return self.logged_in()

    def login(self):
        """Login into moodle. This queries the password but does not store it.

        !!!  USE AT OWN RISK  !!!

        Even though the password is not written to disk explicitly, who knows
        where it is cached to by python.
        """
        login_url = 'https://' + self.domain + '/login/index.php'
        d = {'username': self.username,
             'password': self.configuration
                 .get("MOODLE_PASSWORDS", {})
                 .get(self.username)}
        if d['password'] is None:
            d['password'] = getpass.getpass(
                f'[loggin in as {self.username}] Password: ')
        print(f'INFO: logging in as {self.username} ... ', end='', flush=True)
        # import ipdb; ipdb.set_trace()

        self._last_request = self.session.post(login_url, data=d)
        self.session_state['cookie'] = self.session.cookies['MoodleSession']
        if self.query_logged_in():
            print(f'OK, your full name is "{self.full_name:s}"')
        else:
            print('FAILED')

    @staticmethod
    def dump_dashboard(r):
        """Dump r.text to /tmp/dashboard%03d.html

        For debugging only."""
        for i in itertools.count():
            html_dump_path = f'/tmp/dashboard{i:03d}.html'
            if not os.path.exists(html_dump_path):
                break
        print(f'MoodleSession.scrape_dashboard() -> {html_dump_path}')
        with open(html_dump_path, 'w') as f:
            f.write(r.text)

    def scrape_dashboard(self, r):
        """Scrape the moodle dashboard to retrieve full name, user id and
        session key."""
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
            self.full_name = div[0].find_all('a')[0].text
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
        """Dump the current session's cookie and key to disk."""
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
        """Download all submission of a moodle exercise (usually a zip).

        Returns: Local path of the downloaded file or None, if download failed.
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
        """Open the instant messages moodle view in browser."""
        cmd_line = [self.configuration["FIREFOX_PATH"],
                    self.get_conversation_url(touserid)]
        if os.path.exists(self.configuration["FIREFOX_PATH"]):
            subprocess.call(cmd_line)
        else:
            print("firefox '{}'".format(cmd_line[1]))

    def get_conversation_url(self, touserid):
        """Return the url of the instant message conversation view regarding
        a specific user."""
        return '{}/message/index.php?user={}&id={}'.format(
            self.moodle_base_url, self.userid, touserid)

    def send_instant_message(self, touserid, text):
        """Send an instant message `text` to the user `touserid`.

        Note that text is interpreted as HTML, so literal `<>&`s will need
        to be escaped.

        Returns the text actually sent. In case of failure, returns False.
        """
        try:
            logging.debug(f"touserid {touserid}")
            data = self._ajax_call(
                'core_message_send_instant_messages',
                {"messages": [{"touserid": int(touserid), "text": text}]},
                referer='/message/index.php')[0]
        except (MoodleAjaxError, IndexError):
            logging.error("MoodleAjaxError or IndexError")
            logging.debug(data)
            return False

        if data.get('msgid', -1) > -1:
            logging.debug(data)
            return data.get('text', False)
        
        if data.get('msgid', -1) == -1:
            logging.debug(f"Error: {data.get('errormessage')}")
            error="Die Mitteilung ist länger als erlaubt."
            if data.get('errormessage')==error:
                logging.debug("Spliting Message and send in two parts.")
                half=floor(len(text)/2)
                logging.debug(text[:half])
                logging.debug(len(text[:half]))
                success1=self.send_instant_message(touserid, text[:half])
                if success1!= True:
                    logging.debug("Sending first part failed")
                    return False
                success2=self.send_instant_message(touserid, text[half-10:])
                return success2
        logging.debug(data)
        return False

    def get_current_grading(self, userid, return_editor_itemid=False):
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
        """Make AJAX call through sevice.php."""
        headers = dict(AJAX_HEADERS)
        if referer:
            headers.update({'Referer': 'https://' + self.domain + referer})
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
        """Clear the session variable cache because we are not logged in.
        """
        self.session_state['logged_in'] = False
        self.session_state['cookie'] = ''
        self.session_state['sesskey'] = ''
        self.dump_state()

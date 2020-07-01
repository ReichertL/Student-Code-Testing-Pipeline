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

from models.student import Student
from util.absolute_path_resolver import resolve_absolute_path

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
    def __init__(self, username, session_state, configuration, database_manager, interactive=True):
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
        self.read_users_cached(database_manager)
        self.username = username
        self.session_state = session_state
        if session_state and session_state.get('logged_in'):
            self.session.cookies.set('MoodleSession', session_state['cookie'],
                                     path='/', domain=self.domain)
            self.query_logged_in()
        if interactive:
            if not session_state or not self.session_state['logged_in']:
                self.login()

    def read_users_cached(self, database_manager):
        """Read in the users list found in a cache file 'teilnehmer.json' in
        the current working directory."""
        self.teilnehmer = database_manager.get_all_students()

    def update_teilnehmer(self, database_manager):
        """Fetch moodle course user index and save names and user ids as json.

        course_id defaults to constants.MOODLE_COURSE_ID

        """
        moodle_base_url = 'https://' + self.domain
        course_id = self.configuration["MOODLE_IDS"]["MOODLE_COURSE_ID"]
        re_teilnehmer = re.compile(
            r'<a href="{}/user/view.php\?id=(\d+)&amp;course=(\d+)">'
            r'<img src="[^"]*"\s+class="[^"]*"[^>]*>([^<]+)</a>'.format(
                re.escape(moodle_base_url)))
        res = {}
        url = moodle_base_url + '/user/index.php'
        r = self.session.get(url, params={'id': course_id, 'perpage': '5000'})
        self._last_request = r
        for line in r.text.splitlines():
            mo = re_teilnehmer.search(line)
            if mo:
                id_, course_id, name = mo.group(1, 2, 3)
                res[name] = id_

        print('Found {} Teilnehmer.'.format(len(res)))

        # dump teilnehmer list as json
        if res:
            for i in res:
                Student(i, res[i], database_manager)
        else:
            with open('users.html', 'w') as f:
                f.write(r.text)

    def logged_in(self):
        """Just a shortcut to the session state.

        To re-verify the true logged-in-state, use `query_logged_in` instead.
        """
        return (self.session_state['logged_in']
                and len(self.userid) > 0)

    def query_logged_in(self):
        """Try to fetch and scrape dashboard. We use this to find out,
        whether we are currently logged in."""
        moodle_base_url = 'https://' + self.domain
        r = self.session.get(moodle_base_url + '/my/')
        self.scrape_dashboard(r)
        self._last_request = r
        return self.logged_in

    def login(self):
        """Login into moodle. This queries the password but does not store it.

        !!!  USE AT OWN RISK  !!!

        Even though the password is not written to disk explicitly, who knows
        where it is cached to by python.
        """
        login_url = 'https://' + self.domain + '/login/index.php'
        d = {'username': self.username,
             'password': getpass.getpass(
                 f'[loggin in as {self.username}] Password: ')}
        # import ipdb; ipdb.set_trace()
        self._last_request = self.session.post(login_url, data=d)
        self.session_state['cookie'] = self.session.cookies['MoodleSession']
        self.query_logged_in()

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
        moodle_base_url = 'https://' + self.domain

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
                if mo.group(1) != moodle_base_url + '/user/profile.php?id=':
                    raise MoodleScrapeError(
                        'cannot find link .../user/profile.php?id=...')
                self.userid = mo.group(2)
            else:
                raise MoodleScrapeError(
                    'cannot find link .../user/profile.php?id=...')
            # extract the sesskey
            url = div[0].find_all('a')[1]['href']
            if (mo := re.match(r'(.*?=)(\w+)', url)) is not None:
                if mo.group(1) != moodle_base_url \
                        + '/login/logout.php?sesskey=':
                    raise MoodleScrapeError(
                        'cannot find link .../login/logout.php?sesskey=...')
                self.session_state['sesskey'] = mo.group(2)
            else:
                raise MoodleScrapeError(
                    'cannot find link .../login/logout.php?sesskey=...')
        except (IndexError, MoodleScrapeError) as e:
            sys.stderr.write('ERROR: unexpected error in dashboard parsing')
            std.esterr.write(f'-> {e:s}')
            self.dump_dashboard(r)
            self.session_state['logged_in'] = False
        self.dump_state()

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
        moodle_base_url = 'https://' + self.domain
        if id_ is None:
            id_ = self.configuration["MOODLE_IDS"]["MOODLE_SUBMISSION_ID"]
        dest = self.configuration["SUBMISSION_NEW_ZIP"]
        r = self.session.get(moodle_base_url + '/mod/assign/view.php',
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
        cmd_line = [self.configuration["FIREFOX_PATH"], self.get_conversation_url(touserid)]
        if os.path.exists(self.configuration["FIREFOX_PATH"]):
            subprocess.call(cmd_line)
        else:
            print("firefox '{}'".format(cmd_line[1]))

    def get_conversation_url(self, touserid):
        """Return the url of the instant message conversation view regarding
        a specific user."""
        moodle_base_url = 'https://' + self.domain
        return '{}/message/index.php?user={}&id={}'.format(
            moodle_base_url, self.userid, touserid)

    def send_instant_message(self, touserid, text):
        """Send an instant message `text` to the user `touserid`.

        Note that text is interpreted as HTML, so literal `<>&`s will need
        to be escaped.

        Returns the text actually sent. In case of failure, returns False.
        """
        try:
            data = self._ajax_call(
                'core_message_send_instant_messages',
                {"messages": [{"touserid": int(touserid), "text": text}]})[0]
        except (MoodleAjaxError, IndexError):
            return False
        if data.get('msgid', -1) > -1:
            return data.get('text', False)
        return False

    def _ajax_call(self, methodname: str, args):
        """Make AJAX call through sevice.php."""

        AJAX_HEADERS.update({'Referer': 'https://' + self.domain + '/message/index.php'})
        data = [{"index": 0,
                 "methodname": methodname,
                 "args": args}]
        r = self.session.post(
            self.configuration["AJAX_URL"],
            params={'sesskey': self.session_state['sesskey'],
                    'info': methodname},
            data=json.dumps(data),
            headers={**AJAX_HEADERS,
                     'Referrer': self.configuration["AJAX_URL"]})
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

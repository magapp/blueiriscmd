"""
Python service library for talking to a BlueIris Server

Modified from magapp/blueiriscmd
"""
import logging

import hashlib
import json
import requests

_LOGGER = logging.getLogger(__name__)

SIGNAL_RED = 'red'
SIGNAL_YELLOW = 'yellow'
SIGNAL_GREEN = 'green'

SIGNALS = [SIGNAL_RED, SIGNAL_GREEN, SIGNAL_YELLOW]

PTZ_PAN_LEFT = 0
PTZ_PAN_RIGHT = 1
PTZ_TILT_UP = 2
PTZ_TILT_DOWN = 3
PTZ_CENTER = PTZ_HOME = 4
PTZ_ZOOM_IN = 5
PTZ_ZOOM_OUT = 6
PTZ_POWER_50 = 8
PTZ_POWER_60 = 9
PTZ_POWER_OUTDOOR = 10
PTZ_BRIGHTNESS_0 = 11
PTZ_BRIGHTNESS_1 = 12
PTZ_BRIGHTNESS_2 = 13
PTZ_BRIGHTNESS_3 = 14
PTZ_BRIGHTNESS_4 = 15
PTZ_BRIGHTNESS_5 = 16
PTZ_BRIGHTNESS_6 = 17
PTZ_BRIGHTNESS_7 = 18
PTZ_BRIGHTNESS_8 = 19
PTZ_BRIGHTNESS_9 = 20
PTZ_BRIGHTNESS_10 = 21
PTZ_BRIGHTNESS_11 = 22
PTZ_BRIGHTNESS_12 = 23
PTZ_BRIGHTNESS_13 = 24
PTZ_BRIGHTNESS_14 = 25
PTZ_BRIGHTNESS_15 = 26
PTZ_CONTRAST_0 = 27
PTZ_CONTRAST_1 = 28
PTZ_CONTRAST_2 = 29
PTZ_CONTRAST_3 = 30
PTZ_CONTRAST_4 = 31
PTZ_CONTRAST_5 = 32
PTZ_CONTRAST_6 = 33
PTZ_IR_ON = 34
PTZ_IR_OFF = 35
PTZ_PRESET_1 = 101
PTZ_PRESET_2 = 102
PTZ_PRESET_3 = 103
PTZ_PRESET_4 = 104
PTZ_PRESET_5 = 105
PTZ_PRESET_6 = 106
PTZ_PRESET_7 = 107
PTZ_PRESET_8 = 108
PTZ_PRESET_9 = 109
PTZ_PRESET_10 = 110
PTZ_PRESET_11 = 111
PTZ_PRESET_12 = 112
PTZ_PRESET_13 = 113
PTZ_PRESET_14 = 114
PTZ_PRESET_15 = 115
PTZ_PRESET_16 = 116
PTZ_PRESET_17 = 117
PTZ_PRESET_18 = 118
PTZ_PRESET_19 = 119
PTZ_PRESET_20 = 120

CONFIG_PAUSE_INDEFINITELY = -1
CONFIG_PAUSE_CANCEL = 0
CONFIG_PAUSE_ADD_30_SEC = 1
CONFIG_PAUSE_ADD_1_MIN = 2
CONFIG_PAUSE_ADD_1_HOUR = 3

LOG_SEVERITY_INFO = 'INFO'
LOG_SEVERITY_WARN = 'WARNING'
LOG_SEVERITY_ERROR = 'ERROR'

LOG_SEVERITY = [LOG_SEVERITY_INFO, LOG_SEVERITY_WARN, LOG_SEVERITY_ERROR]

UNKNOWN_DICT = {'-1': ''}
UNKNOWN_LIST = [{'-1': ''}]
UNKNOWN_HASH = -1
UNKNOWN_STRING = "noname"


class BlueIris:

    def __init__(self, user, password, protocol, host, port="", debug=False):
        if port != "":
            host = "{}:{}".format(host, port)
        self.url = "{}://{}/json".format(protocol, host)
        self.user = user
        self.password = password
        self.blueiris_session = UNKNOWN_HASH
        self.response = UNKNOWN_HASH
        self._status = UNKNOWN_DICT
        self._camlist = UNKNOWN_LIST
        self._alertlist = UNKNOWN_LIST
        self._cliplist = UNKNOWN_LIST
        self._profiles = UNKNOWN_LIST
        self._log = UNKNOWN_LIST
        self.session = requests.session()
        self.debug = debug
        """Do login"""
        session_info = self.login()
        if self.debug:
            print("Session info: {}".format(session_info))
        self._name = session_info.get('system name', default=UNKNOWN_STRING)
        self._profiles = session_info.get('profiles', default=UNKNOWN_LIST)
        self._am_admin = session_info.get('admin', default=False)
        self._ptz_allowed = session_info.get('ptz', default=False)
        self._clips_allowed = session_info.get('clips', default=False)
        self._schedules = session_info.get('schedules', default=UNKNOWN_LIST)
        self._version = session_info.get('version', default=UNKNOWN_STRING)
        self.update_status()

    def generate_response(self):
        """Update self.username, self.password and self.blueiris_session before calling this."""
        self.response = hashlib.md5(
            "{}:{}:{}".format(self.user, self.blueiris_session, self.password).encode('utf-8')).hexdigest()

    def update_status(self):
        """Run the command to refresh our stored status"""
        self._status = self.cmd("status")

    def update_camlist(self):
        """Run the command to refresh our stored status"""
        self._camlist = self.cmd("camlist")

    def update_cliplist(self):
        """Run the command to refresh our stored status"""
        self._cliplist = self.cmd("cliplist", {"camera": "index"})

    def update_alertlist(self):
        """Run the command to refresh our stored status"""
        self._alertlist = self.cmd("alertlist", {"camera": "index"})

    def update_log(self):
        """Run the command to refresh our stored log value"""
        self._log = self.cmd("log")

    @property
    def name(self):
        """Return the system name"""
        return self._name

    @property
    def version(self):
        """Return the system version"""
        return self._version

    @property
    def log(self):
        """Return the system log"""
        if self._log == UNKNOWN_LIST:
            self.update_log()
        return self._log

    @property
    def profiles(self):
        """Return the list of profiles"""
        return self._profiles

    @property
    def schedules(self):
        """Return the list of profiles"""
        return self._schedules

    @property
    def cameras(self):
        """Request and return the camera list"""
        if self._camlist == UNKNOWN_LIST:
            self.update_camlist()
        shortlist = []
        for cam in self._camlist:
            if cam.get('optionValue') != 'Index' and cam.get('optionValue') != '@Index':
                shortlist.append({'name': cam.get('optionDisplay'), 'code': cam.get('optionValue')})
        return shortlist

    @property
    def all_alerts(self):
        """Request and return the list of alert pictures"""
        if self._alertlist == UNKNOWN_LIST:
            self.update_alertlist()
        return self._alertlist

    @property
    def all_clips(self):
        """Request and return the list of clips"""
        if self._cliplist == UNKNOWN_LIST:
            self.update_cliplist()
        return self._cliplist

    @property
    def status(self):
        if self._status == UNKNOWN_DICT:
            self.update_status()
        return self._status

    @property
    def profile(self):
        if len(self.status) < 2:
            return "Error"
        profile_id = int(self.status.get('profile'))
        if profile_id == -1:
            return "Undefined"
        return self._profiles[profile_id]

    @property
    def signal(self):
        signal_id = int(self.status.get('signal', default=4))
        return SIGNALS[signal_id]

    def set_signal(self, signal_name):
        if signal_name not in SIGNALS:
            print("Unable to set signal to unknown value {}. (Use the SIGNAL_ constants)".format(signal_name))
        else:
            self.cmd("status", {"signal": SIGNALS.index(signal_name)})

    def set_schedule(self, schedule_name):
        if schedule_name not in self._schedules:
            print("Bad schedule name {}. (Use the .schedules property for a list of options)".format(schedule_name))
        else:
            self.cmd("status", {"schedule": schedule_name})

    def toggle_schedule_hold(self):
        self.cmd("status", {"schedule": -1})

    def logout(self):
        self.cmd("logout")

    def login(self):
        """
        Send hashed username/password to validate session
        Returns system name and dictionary of profiles OR nothing
        """
        r = self.session.post(self.url, data=json.dumps({"cmd": "login"}))
        if r.status_code != 200:
            print("Bad response ({}) when trying to contact {}, {}".format(r.status_code, self.url, r.text))
        else:
            self.blueiris_session = r.json()["session"]
            self.generate_response()
            r = self.session.post(self.url,
                                  data=json.dumps(
                                      {"cmd": "login", "session": self.blueiris_session, "response": self.response}))
            if r.status_code != 200 or r.json()["result"] != "success":
                print("Bad login {} :{}".format(r.status_code, r.text))
            else:
                return r.json()["data"]

    def cmd(self, cmd, params=None):
        if params is None:
            params = dict()
        args = {"session": self.blueiris_session, "response": self.response, "cmd": cmd}
        args.update(params)

        r = self.session.post(self.url, data=json.dumps(args))
        if r.status_code != 200:
            print("Unsuccessful response. {}:{}".format(r.status_code, r.text))
            return dict()

        if self.debug:
            print(str(r.json()))

        try:
            return r.json()["data"]
        except KeyError:
            """It's possible that there was no data to be returned. In that case respond 'None'"""
            if r.json()["result"] == "success":
                return "None"
            """Respond with 'Error' in the event we get here and had a bad result"""
            return "Error"

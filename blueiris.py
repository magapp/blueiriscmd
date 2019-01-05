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


class BlueIris:

    def __init__(self, user, password, protocol, host, port="", debug=False):
        if port != "":
            host = "{}:{}".format(host, port)

        self.debug = debug
        self.url = "{}://{}/json".format(protocol, host)
        self.session = requests.session()

        """Send login command"""
        r = self.session.post(self.url, data=json.dumps({"cmd": "login"}))
        if r.status_code != 200:
            print("Unsuccessful response. {}:{}".format(r.status_code, r.text))

        """Calculate login response"""
        self.sessionid = r.json()["session"]
        self.response = hashlib.md5("{}:{}:{}".format(user, self.sessionid, password).encode('utf-8')).hexdigest()
        if self.debug:
            print("session: {} response: {}".format(self.sessionid, self.response))

        self.login()

    @property
    def name(self):
        """Return the system name"""
        return self._system_name

    @property
    def profiles_list(self):
        """Return the list of profiles"""
        return self._profiles_list

    @property
    def camera_list(self):
        """Return the list of profiles"""
        r = self.cmd("camlist")
        return r

    @property
    def alert_list(self):
        """Return the list of alert pictures"""
        r = self.cmd("alertlist", {"camera": "index"})
        return r

    @property
    def clip_list(self):
        """Return the list of alert pictures"""
        r = self.cmd("cliplist", {"camera": "index"})
        return r

    @property
    def status(self):
        r = self.cmd("status")
        return r

    @property
    def active_profile(self):
        profile_id = int(self.status.get('profile'))
        if profile_id == -1:
            return "Undefined"
        return self._profiles_list[profile_id]

    @property
    def active_signal(self):
        signal_id = int(self.status.get('signal'))
        return SIGNALS[signal_id]

    def set_signal(self, signal_name):
        signal_id = SIGNALS.index(signal_name)
        self.cmd("status", {"signal": signal_id})

    def set_schedule(self, schedule_name):
        self.cmd("status", {"schedule": schedule_name})

    def logout(self):
        self.cmd("logout")

    def cmd(self, cmd, params=None):
        if params is None:
            params = dict()
        args = {"session": self.sessionid, "response": self.response, "cmd": cmd}
        args.update(params)

        r = self.session.post(self.url, data=json.dumps(args))
        if r.status_code != 200:
            print("Unsuccessful response. {}:{}".format(r.status_code, r.text))

        if self.debug:
            print(str(r.json()))

        try:
            return r.json()["data"]
        except KeyError:
            """It's possible that there was no data to be returned. In that case respond 'None'"""
            if r.json()["result"] == "success":
                return "None"
            """Respond with 'Error' in the even we get here and had a bad result"""
            return "Error"

    def login(self):
        """Send hashed username/password to validate session"""
        r = self.session.post(self.url,
                              data=json.dumps({"cmd": "login", "session": self.sessionid, "response": self.response}))
        if r.status_code != 200 or r.json()["result"] != "success":
            print("Unsuccessful response {} :{}".format(r.status_code, r.text))
        else:
            self._system_name = r.json()["data"]["system name"]
            self._profiles_list = r.json()["data"]["profiles"]

            print("Connected to '{}'".format(self._system_name))

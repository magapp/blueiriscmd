"""
Python service library for talking to a BlueIris Server

Modified from magapp/blueiriscmd
"""
import logging

import hashlib
import json
import requests

_LOGGER = logging.getLogger(__name__)

SIGNALS = ['red', 'green', 'yellow']

class BlueIris:

    def __init__(self, protocol, host, user, password, debug=False):
        self.debug = debug
        self.url = "{}://{}/json".format(protocol, host)
        self.session = requests.session()

        """Send login command"""
        r = self.session.post(self.url, data=json.dumps({"cmd": "login"}))
        self.status = r.status_code
        if r.status_code != 200:
            _LOGGER.error("Unsuccessful response. {}:{}".format(r.status_code, r.text))

        """Calculate login response"""
        self.sessionid = r.json()["session"]
        self.response = hashlib.md5("{}:{}:{}".format(user, self.sessionid, password).encode('utf-8')).hexdigest()
        if self.debug:
            _LOGGER.debug("session: {} response: {}".format(self.sessionid, self.response))
        """Send hashed username/password to validate session"""
        r = self.session.post(self.url,
                              data=json.dumps({"cmd": "login", "session": self.sessionid, "response": self.response}))
        self.status = r.status_code
        if r.status_code != 200 or r.json()["result"] != "success":
            _LOGGER.error("Unsuccessful response. {}:{}".format(r.status_code, r.text))
        else:
            self._system_name = r.json()["data"]["system name"]
            self._profiles_list = r.json()["data"]["profiles"]

            _LOGGER.info("Connected to '{}'".format(self._system_name))

    @property
    def system_name(self):
        """Return the system name"""
        return self._system_name

    @property
    def profiles_list(self):
        """Return the list of profiles"""
        return self._profiles_list

    @property
    def active_profile(self):
        r = self.cmd("status")
        profile_id = int(r["profile"])
        if profile_id == -1:
            return "Undefined"
        return self._profiles_list[profile_id]

    @property
    def active_signal(self):
        r = self.cmd("status")
        signal_id = int(r["signal"])
        return SIGNALS[signal_id]

    @property
    def active_schedule(self):
        r = self.cmd("status")
        schedule = r["schedule"]
        return schedule

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
        self.status = r.status_code
        if r.status_code != 200:
            _LOGGER.error("Unsuccessful response. {}:{}".format(r.status_code, r.text))

        if self.debug:
            _LOGGER.debug(str(r.json()))

        try:
            return r.json()["data"]
        except KeyError:
            return r.json()

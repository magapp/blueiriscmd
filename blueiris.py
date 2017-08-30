#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Magnus Appelquist 2014-06-02 Initial
#

import requests, json, hashlib, sys, argparse

def main():
    parser = argparse.ArgumentParser(description='Blue Iris controller', prog='blueiris')

    parser.add_argument('--version', action='version', version='%(prog)s 1.0 https://github.com/magapp/blueiris')
    parser.add_argument("--host", help="Blue Iris host to connect to ", required=True)
    parser.add_argument('--user', help='User to use when connecting', required=True)
    parser.add_argument('--password', help='Password to use when connecting', required=True)
    parser.add_argument('--debug', action='store_true', help='Print debug messages')
    parser.add_argument('--list-profiles', action='store_true', help='List all available profiles')
    parser.add_argument('--set-profile', action='store', help='Set current profile', metavar='profile-name', default=None)
    parser.add_argument('--set-schedule', action='store', help='Set current schedule', metavar='schedule-name', default=None)
    parser.add_argument('--set-signal', action='store', help='Set current signal', metavar='signal-name', default=None, choices=['red','yellow','green'])
    parser.add_argument('--trigger', action='store', help='Trigger camera', metavar='camera-short-name', default=None)

    args = parser.parse_args()

    bi = BlueIris(args.host, args.user, args.password, args.debug)
    print "Profile '%s' is active" % bi.get_profile()
    print "Schedule '%s' is active" % bi.get_schedule()
    print "Signal is %s" % bi.get_signal()

    if args.list_profiles:
        print "Available profiles are:"
        print ", ".join(bi.profiles_list)

    if args.set_profile:
        try:
            profile_id = bi.profiles_list.index(args.set_profile)
        except:
            print "Could not find any profile with that name. Use --list-profiles to see available profiles."
            sys.exit(0)
        print "Setting active profile to '%s' (id: %d)" % (args.set_profile, profile_id)
        bi.cmd("status", {"profile": profile_id})

    if args.set_signal:
        signal = bi.get_signal()
        print "Switching signal %s -> %s" % (signal, args.set_signal)
        bi.set_signal(args.set_signal)

    if args.set_schedule:
        schedule = bi.get_schedule()
        print "Switching schedule %s -> %s" % (schedule, args.set_schedule)
        bi.set_schedule(args.set_schedule)

    if args.trigger:
        print "Triggering camera '%s'" % args.trigger
        bi.cmd("trigger", {"camera": args.trigger})

    bi.logout()
    sys.exit(0)

class BlueIris:
    session = None
    response = None
    signals = ['red', 'green', 'yellow']

    def __init__(self, host, user, password, debug=False):
        self.host = host
        self.user = user
        self.password = password
        self.debug = debug
        self.url = "http://"+host+"/json"
        r = requests.post(self.url, data=json.dumps({"cmd":"login"}))
        if r.status_code != 200:
            print r.status_code
            print r.text
            sys.exit(1)

        self.session = r.json()["session"]
        self.response = hashlib.md5("%s:%s:%s" % (user, self.session, password)).hexdigest()
        if self.debug:
            print "session: %s response: %s" % (self.session, self.response)

        r = requests.post(self.url, data=json.dumps({"cmd":"login", "session": self.session, "response": self.response}))
        if r.status_code != 200 or r.json()["result"] != "success":
            print r.status_code
            print r.text
            sys.exit(1)
        self.system_name = r.json()["data"]["system name"]
        self.profiles_list = r.json()["data"]["profiles"]

        print "Connected to '%s'" % self.system_name

    def cmd(self, cmd, params=dict()):
        args = {"session": self.session, "response": self.response, "cmd": cmd}
        args.update(params)

        # print self.url
        # print json.dumps(args)
        r = requests.post(self.url, data=json.dumps(args))

        # if r.status_code != 200 or r.json()["result"] != "success":
        if r.status_code != 200:
            print r.status_code
            print r.text
            sys.exit(1)

        if self.debug:
            print str(r.json())

        try:
            return r.json()["data"]
        except:
            return r.json()

    def get_profile(self):
        r = self.cmd("status")
        profile_id = int(r["profile"])
        if profile_id == -1:
            return "Undefined"
        return self.profiles_list[profile_id]

    def get_signal(self):
        r = self.cmd("status")
        signal_id = int(r["signal"])
        return self.signals[signal_id]

    def get_schedule(self):
        r = self.cmd("status")
        schedule = r["schedule"]
        return schedule

    def set_signal(self, signal_name):
        signal_id = self.signals.index(signal_name)
        self.cmd("status", {"signal": signal_id})

    def set_schedule(self, schedule_name):
        self.cmd("status", {"schedule": schedule_name})

    def logout(self):
        self.cmd("logout")

if __name__ == "__main__":
    main()

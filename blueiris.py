#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Magnus Appelquist 2014-06-02 Initial
#

import requests, json, hashlib, sys, argparse

def main():
    parser = argparse.ArgumentParser(description='Blue Iris controller', prog='blueiris')

    parser.add_argument('--version', action='version', version='%(prog)s 1.0 https://github.com/magapp/blueiriscmd')
    parser.add_argument("--host", help="Blue Iris host to connect to ", required=True)
    parser.add_argument('--user', help='User to use when connecting', required=True)
    parser.add_argument('--password', help='Password to use when connecting', required=True)
    parser.add_argument('--debug', action='store_true', help='Print debug messages')
    parser.add_argument('--list-profiles', action='store_true', help='List all available profiles')
    parser.add_argument('--set-profile', action='store', help='Set current profile', metavar='profile-name', default=None)
    parser.add_argument('--set-schedule', action='store', help='Set current schedule', metavar='schedule-name', default=None)
    parser.add_argument('--set-signal', action='store', help='Set current signal', metavar='signal-name', default=None, choices=['red','yellow','green'])
    parser.add_argument('--trigger', action='store', help='Trigger camera', metavar='camera-short-name', default=None)
    parser.add_argument('--ptzbutton', action='store', help='Send PTZ Button Number', metavar='ptz-button-name', default=None)
    parser.add_argument('--ptzcam', action='store', help='Send PTZ Command', metavar='ptz-cam-name', default=None)

    args = parser.parse_args()

    bi = BlueIris(args.host, args.user, args.password, args.debug)
    print(f"Profile '{bi.get_profile()}' is active")
    print(f"Schedule '{bi.get_schedule()}' is active")
    print(f"Signal is {bi.get_signal()}")

    if args.list_profiles:
        print("Available profiles are:")
        print(", ".join(bi.profiles_list))

    if args.set_profile:
        try:
            profile_id = bi.profiles_list.index(args.set_profile)
        except:
            print("Could not find any profile with that name. Use --list-profiles to see available profiles.")
            sys.exit(0)
        print(f"Setting active profile to '{args.set_profile}' (id: {profile_id})")
        bi.cmd("status", {"profile": profile_id})

    if args.set_signal:
        signal = bi.get_signal()
        print(f"Switching signal {signal} -> {args.set_signal}")
        bi.set_signal(args.set_signal)

    if args.set_schedule:
        schedule = bi.get_schedule()
        print(f"Switching schedule {schedule} -> {args.set_schedule}")
        bi.set_schedule(args.set_schedule)

    if args.trigger:
        print(f"Triggering camera '{args.trigger}'")
        bi.cmd("trigger", {"camera": args.trigger})

    if args.ptzbutton:
        #0: Pan left
        #1: Pan right
        #2: Tilt up
        #3: Tilt down
        #4: Center or home (if supported by camera)
        #5: Zoom in
        #6: Zoom out
        #8..10: Power mode, 50, 60, or outdoor
        #11..26: Brightness 0-15
        #27..33: Contrast 0-6
        #34..35: IR on, off
        #101..120: Go to preset position 1..20
        if not args.ptzcam:
            print("Using --ptzcmdnum requires argument --ptzcam with valid Cam Name..")
            sys.exit(0)
        print(f"Sending PTZ Command Button: '{args.ptzbutton}' to Cam: '{args.ptzcam}'")
        bi.cmd("ptz", {"camera": args.ptzcam,"button": int(args.ptzbutton),"updown": 0})

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
            print(r.status_code)
            print(r.text)
            sys.exit(1)

        self.session = r.json()["session"]
        self.response = hashlib.md5(f"{user}:{self.session}:{password}".encode('utf-8')).hexdigest()
        if self.debug:
            print(f"session: '{self.session}'' response: '{self.response}'")

        r = requests.post(self.url, data=json.dumps({"cmd":"login", "session": self.session, "response": self.response}))
        if r.status_code != 200 or r.json()["result"] != "success":
            print(r.status_code)
            print(r.text)
            sys.exit(1)
        self.system_name = r.json()["data"]["system name"]
        self.profiles_list = r.json()["data"]["profiles"]

        print(f"Connected to '{self.system_name}'")

    def cmd(self, cmd, params=dict()):
        args = {"session": self.session, "cmd": cmd}
        args.update(params)

        # print(self.url)
        # print("Sending Data: ")
        # print(json.dumps(args))
        r = requests.post(self.url, data=json.dumps(args))

        if r.status_code != 200:
            print(r.status_code)
            print(r.text)
            sys.exit(1)
        else:
            pass
            #print "success: " + str(r.status_code)
            #print r.text

        if self.debug:
            print(str(r.json()))

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

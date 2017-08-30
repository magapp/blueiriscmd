blueiriscmd
===========

Python cmd tool that talk with Blue Iris Camera surveillance software API.

Blue Iris have an API that allows other programs to read status, trigger events, change profile, set signal, schedule and such. This python tool gives you a command line tool that can be used.

Example to change current profile to "Home":

    blueiris.py --host 192.168.1.100 --user username --password password  --set-profile Home
    Connected to 'My place'
    Profile 'Away' is active
    Setting active profile to 'Home' (id: 2)

This command will trigger event on camera "garage":

    blueiris.py --host 192.168.1.100 --user username --password password --trigger garage
    Connected to 'My place'
    Profile 'Borta' is active
    Triggering camera 'garage'

I use this to change profile from my home alarm system automaticlly, and also to trigger cameras from PIR connected to a Raspberry Pi.

Full API is not implemented, but feel free to add what you miss.

More information regarding Blue Iris can be found here:
http://blueirissoftware.com/



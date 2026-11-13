"""Which devices this build holds (decision 0032 item 8).

`tools.publish --bundle NAME` writes its own copy of this file into the build. This copy, the one
in the repo, lists every built device, so the tests and `flet run` behave as the all-in-one app.
"""

NAME = "all"
DEVICES = ("nspire",)

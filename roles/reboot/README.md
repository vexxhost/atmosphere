# `reboot`

This is an operational role that will run a set of checks to verify that the
server is safe to reboot.  If the checks pass, a silence will be created to
prevent alarms from firing during the reboot.   Once that's done, the reboot
will start and the silence will be removed once the server is back online.

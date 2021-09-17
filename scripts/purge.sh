#!/bin/sh
# Remove BiscuitWM
rm -r /usr/bin/biscuitwm-src
rm /usr/bin/biscuitwm
# Remove session entry
rm /usr/bin/biscuitwm-session
rm /usr/share/xsessions/biscuitwm-session.desktop
# Remove config file
rm -r /etc/biscuitwm

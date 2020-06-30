#!/bin/sh
# Copy BiscuitWM
cp src/biscuitwm.py /usr/bin/biscuitwm.py
cp assets/biscuitwm /usr/bin/biscuitwm
# Copy BiscuitBar
# cp src/biscuitbar.py /usr/bin/biscuitbar.py
# cp assets/biscuitbar /usr/bin/biscuitbar
# Copy session entries
cp assets/biscuitwm-session /usr/bin/biscuitwm-session
cp assets/biscuitwm-session.desktop /usr/share/xsessions/biscuitwm-session.desktop
# Set permissions
chmod a+x /usr/bin/biscuitwm
# chmod a+x /usr/bin/biscuitbar
chmod a+x /usr/bin/biscuitwm-session

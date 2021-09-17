#!/bin/sh

# Copy BiscuitWM
mkdir /usr/bin/biscuitwm-src
cp -r src/* /usr/bin/biscuitwm-src/
cp assets/biscuitwm /usr/bin/biscuitwm
# Copy session entries
cp assets/biscuitwm-session /usr/bin/biscuitwm-session
cp assets/biscuitwm-session.desktop /usr/share/xsessions/biscuitwm-session.desktop
# Create config folder
mkdir /etc/biscuitwm
cp assets/biscuitwm.json /etc/biscuitwm/biscuitwm.json
# Set permissions
chmod a+x /usr/bin/biscuitwm
chmod a+x /usr/bin/biscuitwm-session

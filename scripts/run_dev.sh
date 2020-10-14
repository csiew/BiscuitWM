#!/bin/sh
sh biscuitwm-uninstall.sh
sh biscuitwm-install.sh
DISPLAY=:0
Xephyr -br -ac -noreset -screen 1024x780 :1 &

#!/bin/sh
cp src/biscuitwm.py /usr/bin/biscuitwm.py
DISPLAY=:0
Xephyr -br -ac -noreset -screen 1024x780 :1 &

#!/bin/sh
sh purge.sh
sh setup.sh
DISPLAY=:0
Xephyr -br -ac -noreset -screen 1024x780 :1 &

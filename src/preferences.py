import os
import json

from globals import *


class Preferences(object):
    def __init__(self):
        self.dev = {
            "debug": 1
        }
        self.placement = {
            "auto_window_placement": 1,
            "auto_window_fit": 1,
            "auto_window_raise": 1,
            "center_window_placement": 1
        }
        self.deskbar = {
            "enabled": 1,
            "background_color": "white",
            "foreground_color": "black",
            "clock": {
                "enabled": 1,
                "show_day": 1,
                "show_date": 1,
                "show_seconds": 1
            }
        }
        self.xround = {
            "enabled": 1
        }
        self.appearance = {
            "window_border_width": 2,
            "active_window_border_color": "sienna",
            "inactive_window_border_color": "black",
            "background_color": "#D2B48C"
        }

        self.categories = ["dev", "placement", "deskbar", "xround", "appearance"]
        self.read_config(ignore=False)

    def read_config(self, ignore=False):
        if ignore is False:
            if os.path.exists(CONFIG_FILE_PATH):
                with open(CONFIG_FILE_PATH, "r") as user_prefs:
                    user_prefs = json.load(user_prefs)
                    user_prefs_keys = [*user_prefs.keys()]
                    if user_prefs_keys.sort() == self.categories.sort():
                        print("Config file has matching keys")
                        self.dev = user_prefs["dev"]
                        self.placement = user_prefs["placement"]
                        self.deskbar = user_prefs["deskbar"]
                        self.xround = user_prefs["xround"]
                        self.appearance = user_prefs["appearance"]
                    else:
                        print("Config file does not having matching keys!")
            else:
                print("Config file not found!")
        else:
            print("Ignoring config file... using defaults")

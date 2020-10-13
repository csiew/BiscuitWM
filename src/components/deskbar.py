import os
from Xlib import X, Xatom
from x11util import load_font
from models.pixel_palette import PixelPalette
from utils.repeated_timer import RepeatedTimer
from components.deskbar_item import DeskbarItem

from globals import *


class Deskbar(object):
    def __init__(
            self, ewmh, dpy, dpy_root, screen, display_dimensions,
            wm_window_type, wm_window_types, wm_state, wm_window_status,
            prefs, session_info
    ):
        self.ewmh = ewmh
        self.dpy = dpy
        self.dpy_root = dpy_root
        self.screen = screen
        self.colormap = self.screen.default_colormap
        self.pixel_palette = PixelPalette(self.colormap)
        self.system_font = load_font(self.dpy, FONT_NAME)
        self.display_dimensions = display_dimensions

        self.wm_window_type = wm_window_type
        self.wm_window_types = wm_window_types
        self.wm_state = wm_state
        self.wm_window_status = wm_window_status

        self.prefs = prefs
        self.session_info = session_info
        self.time_command = self.set_get_current_time_command()

        self.border_width = 1
        self.height = 20
        self.real_height = self.height + self.border_width

        self.text_y_alignment = 15
        self.padding_leading = 15
        self.padding_between = 20
        self.padding_trailing = 15
        self.color_scheme = self.get_deskbar_color_scheme()

        self.command_string = ""

        self.deskbar = None
        self.deskbar_gc = None

        self.deskbar_items = {
            "leading": {
                "active_window_title": DeskbarItem(
                    "Window Title",
                    text=self.session_info.session_name
                ),
                "window_count": DeskbarItem(
                    "Window Count",
                    text="0 windows",
                    enabled=False
                ),
                "launcher": DeskbarItem(
                    "Launcher",
                    text=self.command_string,
                    enabled=False
                )
            },
            "trailing": {
                "memory_usage": DeskbarItem(
                    "Memory Usage",
                    interval=10,
                    function=self.set_memory_usage
                ),
                "timestamp": DeskbarItem(
                    "Clock",
                    interval=1 if self.prefs.deskbar["clock"]["show_seconds"] == 1 else 30,
                    function=self.set_timestamp,
                    enabled=self.prefs.deskbar["clock"]["enabled"] == 1
                ),
            },
        }

        # Leading items drawn from left to right
        # Trailing items drawn from right to left
        self.deskbar_items_order = {
            "leading": ["window_count", "active_window_title", "launcher"],
            "trailing": ["timestamp", "memory_usage"]
        }

        self.deskbar_update_rt = RepeatedTimer(1, self.update)

    def launcher_is_running(self):
        return self.deskbar_items["leading"]["launcher"].enabled

    def toggle_launcher(self, state=False):
        print("Deskbar launcher mode: " + str(state))
        self.deskbar_items["leading"]["launcher"].enabled = state
        self.command_string = ""
        self.update()

    def set_active_window_title(self, window_title):
        if window_title is None or len(window_title) == 0:
            window_title = self.session_info.session_name
        self.deskbar_items["leading"]["active_window_title"].text = window_title
        self.deskbar_items["leading"]["active_window_title"].width = self.get_string_physical_width(window_title)

    def set_window_count(self, window_count):
        suffix = " windows"
        if window_count == 1:
            suffix = " window"
        window_count_string = str(window_count) + suffix
        self.deskbar_items["leading"]["window_count"].text = window_count_string
        self.deskbar_items["leading"]["active_window_title"].width = self.get_string_physical_width(window_count_string)

    def set_memory_usage(self):
        self.deskbar_items["trailing"]["memory_usage"].text = "MEM: " + self.get_memory_usage() + "%"
        self.deskbar_items["trailing"]["memory_usage"].width = self.get_string_physical_width(
            self.deskbar_items["trailing"]["memory_usage"].text)

    def set_timestamp(self):
        self.deskbar_items["trailing"]["timestamp"].text = self.get_current_time()
        self.deskbar_items["trailing"]["timestamp"].width = self.get_string_physical_width(
            self.deskbar_items["trailing"]["timestamp"].text
        )

    def set_get_current_time_command(self):
        command = 'date +"'
        if self.prefs.deskbar["clock"]["show_day"] == 1:
            command += '%a '
        if self.prefs.deskbar["clock"]["show_date"] == 1:
            command += '%d %b '
        command += '%I:%M'
        if self.prefs.deskbar["clock"]["show_seconds"] == 1:
            command += ':%S'
        command += ' %P"'
        return command

    def get_string_physical_width(self, text):
        font = self.dpy.open_font(FONT_NAME)
        result = font.query_text_extents(text.encode())
        return result.overall_width

    def get_memory_usage(self):
        return os.popen("free -m | awk 'NR==2{printf $3*100/$2}' | xargs printf '%.2f'").read()[:-1]

    def get_current_time(self):
        return os.popen(self.time_command).read()[:-1]

    def start_repeated_events(self):
        for item in self.deskbar_items["leading"].values():
            item.start()
        for item in self.deskbar_items["trailing"].values():
            item.start()
        self.deskbar_update_rt.start()

    def stop_repeated_events(self):
        for item in self.deskbar_items["leading"].values():
            item.stop()
        for item in self.deskbar_items["trailing"].values():
            item.stop()
        self.deskbar_update_rt.stop()

    def get_deskbar_color_scheme(self):
        background_pixel = self.pixel_palette.get_named_pixel("white")
        foreground_pixel = self.pixel_palette.get_named_pixel("black")
        if self.prefs.deskbar["foreground_color"] in self.pixel_palette.hex_map.keys():
            foreground_pixel = self.pixel_palette.get_named_pixel(self.prefs.deskbar["foreground_color"])
        elif self.pixel_palette.is_color_hex(self.prefs.deskbar["foreground_color"]) is True:
            foreground_pixel = self.pixel_palette.get_hex_pixel(self.prefs.deskbar["foreground_color"])
        if self.prefs.deskbar["background_color"] in self.pixel_palette.hex_map.keys():
            background_pixel = self.pixel_palette.get_named_pixel(self.prefs.deskbar["background_color"])
        elif self.pixel_palette.is_color_hex(self.prefs.deskbar["background_color"]) is True:
            background_pixel = self.pixel_palette.get_hex_pixel(self.prefs.deskbar["background_color"])

        return {
            "bg": background_pixel,
            "fg": foreground_pixel
        }

    def draw(self):
        screen_width, screen_height = self.display_dimensions.width, self.display_dimensions.height
        background_pixel, foreground_pixel = self.color_scheme["bg"], self.color_scheme["fg"]

        self.deskbar = self.dpy_root.create_window(
            -self.border_width, -self.border_width, screen_width, self.height, self.border_width,
            self.screen.root_depth,
            background_pixel=background_pixel,
            event_mask=X.StructureNotifyMask | X.ExposureMask | X.ButtonPressMask | X.ButtonReleaseMask,
        )
        self.deskbar_gc = self.deskbar.create_gc(
            font=self.system_font,
            foreground=foreground_pixel,
            background=background_pixel,
        )

        self.deskbar.change_property(
            self.wm_window_type,
            Xatom.ATOM,
            32,
            [self.wm_window_types["dock"]],
            X.PropModeReplace
        )
        self.ewmh.setWmState(self.deskbar, 1, "_NET_WM_DESKTOP")
        self.ewmh.setWmState(self.deskbar, 1, "_NET_WM_STATE_SKIP_TASKBAR")
        self.ewmh.setWmState(self.deskbar, 1, "_NET_WM_STATE_ABOVE")

        self.deskbar.map()  # Draw deskbar
        self.set_timestamp()  # Set initial timestamp
        self.set_memory_usage()  # Set initial memory usage percentage
        self.update()  # Initial update
        self.start_repeated_events()  # Start deskbar updates

    def update(self):
        self.deskbar.clear_area()

        # Leading items
        if self.deskbar_items["leading"]["launcher"].enabled is False:
            for item_key in self.deskbar_items_order["leading"]:
                item = self.deskbar_items["leading"][item_key]
                if item.enabled is True:
                    self.deskbar.draw_text(
                        self.deskbar_gc,
                        self.padding_leading,
                        self.text_y_alignment,
                        item.text.encode('utf-8')
                    )
        else:
            # Launcher takes precedence
            self.deskbar.draw_text(
                self.deskbar_gc,
                self.padding_leading,
                self.text_y_alignment,
                (self.command_string + "|").encode('utf-8')
            )

        # Trailing items
        spacing_from_trailing_end = self.padding_trailing
        for item_key in self.deskbar_items_order["trailing"]:
            item = self.deskbar_items["trailing"][item_key]
            if item.enabled is True:
                self.deskbar.draw_text(
                    self.deskbar_gc,
                    self.display_dimensions.width - (item.width + spacing_from_trailing_end),
                    self.text_y_alignment,
                    item.text.encode('utf-8')
                )
                spacing_from_trailing_end += (item.width + self.padding_between)

    def toggle_window_count(self):
        self.deskbar_items["leading"]["window_count"].enabled = not self.deskbar_items["leading"]["window_count"].enabled
        self.deskbar_items["leading"]["active_window_title"].enabled = not self.deskbar_items["leading"]["window_count"].enabled

import os
import sys
import subprocess
from Xlib import X, display, XK, Xatom, Xcursorfont, error
from x11util import load_font
from ewmh import EWMH

import key_combs
from globals import *
from models.window_stack import WindowStack
from models.pixel_palette import PixelPalette
from utils.repeated_timer import RepeatedTimer
from components.deskbar import Deskbar
from utils.display_corners import DisplayCorners


def run_command(command_string):
    try:
        subprocess.Popen(command_string.lstrip(' '), stdout=subprocess.PIPE)
    except Exception as e:
        print(e)


class WindowManager(object):
    def __init__(self, prefs, session_info):
        self.prefs = prefs
        self.session_info = session_info
        self.ewmh = EWMH()
        self.dpy = display.Display()
        self.screen = self.dpy.screen()
        self.dpy_root = self.screen.root
        self.colormap = self.screen.default_colormap
        self.pixel_palette = PixelPalette(self.colormap)

        self.display_dimensions = self.get_display_geometry()
        self.window_resize_options = [
            "center",
            "maximize",
            "left",
            "right",
            "top",
            "bottom"
        ]

        self.managed_windows = []
        self.exposed_windows = []
        self.last_raised_window = None
        self.active_window_title = self.session_info.session_name
        self.window_order = -1

        self.key_alias = {}
        self.keys_down = set()
        self.current_modifier_keys = set()

        self.start = None
        self.attr = None

        self.wm_window_type = self.dpy.intern_atom('_NET_WM_WINDOW_TYPE')
        self.wm_state = self.dpy.intern_atom('_NET_WM_STATE')
        self.wm_window_types = {
            "dock": self.dpy.intern_atom('_NET_WM_WINDOW_TYPE_DOCK'),
            "normal": self.dpy.intern_atom('_NET_WM_WINDOW_TYPE_NORMAL'),
            "dialog": self.dpy.intern_atom('_NET_WM_WINDOW_TYPE_DIALOG'),
            "utility": self.dpy.intern_atom('_NET_WM_WINDOW_TYPE_UTILITY'),
            "toolbar": self.dpy.intern_atom('_NET_WM_WINDOW_TYPE_TOOLBAR'),
            "menu": self.dpy.intern_atom('_NET_WM_WINDOW_TYPE_MENU'),
            "splash": self.dpy.intern_atom('_NET_WM_WINDOW_TYPE_SPLASH')
        }
        self.wm_window_status = {
            "active": self.dpy.intern_atom('_NET_ACTIVE_WINDOW'),
            "desktop": self.dpy.intern_atom('_NET_WM_DESKTOP'),
            "above": self.dpy.intern_atom('_NET_WM_STATE_ABOVE'),
            "skip_taskbar": self.dpy.intern_atom('_NET_WM_STATE_SKIP_TASKBAR'),
            "maximize_vertical": self.dpy.intern_atom('_NET_WM_STATE_MAXIMIZED_VERT'),
            "maximize_horizontal": self.dpy.intern_atom('_NET_WM_STATE_MAXIMIZED_HORIZ')
        }

        self.wm_window_cyclical = [
            self.wm_window_types["normal"],
            self.wm_window_types["dialog"],
            self.wm_window_types["utility"],
            self.wm_window_types["toolbar"]
        ]

        self.deskbar = None
        self.display_corners = None

        self.update_active_window_title_rt = RepeatedTimer(interval=1, function=self.update_active_window_title)
        self.update_active_window_title_rt.stop()

        self.set_cursor(self.dpy_root)
        XK.load_keysym_group('xf86')
        self.set_key_aliases()

    ### QUERY METHODS

    def get_display_geometry(self):
        return self.dpy_root.get_geometry()

    def window_list(self):
        return self.dpy_root.query_tree().children

    def is_managed_window(self, window):
        return window in self.managed_windows

    def is_alive_window(self, window):
        windows = self.dpy_root.query_tree().children
        return window in windows

    def is_dock(self, window):
        result = None
        try:
            result = window.get_full_property(self.wm_window_type, Xatom.ATOM)
        except error.BadWindow or RuntimeError:
            print("Failed to detect if window is dock")
            pass
        if result is not None and result.value[0] == self.wm_window_types["dock"]:
            return True
        return False

    def is_popup_window(self, window):
        result = None
        try:
            result = window.get_full_property(self.wm_window_type, Xatom.ATOM)
        except error.BadWindow or RuntimeError:
            print("Failed to detect if window is dock")
            pass
        if result is not None and (
                result.value[0] == self.wm_window_types["menu"] or result.value[0] == self.wm_window_types["splash"]):
            return True
        return False

    def is_cyclical_window(self, window):
        result = None
        try:
            result = window.get_full_property(self.wm_window_type, Xatom.ATOM)
        except error.BadWindow or RuntimeError:
            print("Failed to detect if window is dock")
            pass
        if result is not None and result.value[0] in self.wm_window_cyclical:
            return True
        return False

    def is_active(self, atom):
        if atom == self.wm_window_status["active"]:
            return True
        return False

    def get_active_window(self):
        window = None
        try:
            window = self.dpy_root.get_full_property(self.wm_window_status["active"], Xatom.ATOM)
        except:
            print("Failed to get active window")
            pass
        return window

    def get_window_class(self, window):
        try:
            cmd, cls = window.get_wm_class()
        except:
            return ''
        if cls is not None:
            return cls
        else:
            return ''

    def get_window_geometry(self, window):
        try:
            return window.get_geometry()
        except:
            return None

    def get_maximum_available_geometry(self):
        window_width = self.display_dimensions.width
        window_height = self.display_dimensions.height
        if self.deskbar is not None:
            window_height -= self.deskbar.real_height
        return window_width, window_height, self.deskbar is not None

    def get_window_attributes(self, window):
        try:
            return window.get_attributes()
        except:
            return None

    def get_window_state(self, window):
        return self.ewmh.getWmState(window, str=True)

    def get_window_shortname(self, window):
        return '0x{:x} [{}]'.format(window.id, self.get_window_class(window))

    def get_window_title(self, window):
        result = None
        try:
            result = window.get_wm_name()
        except:
            pass
        if result is None:
            return self.session_info.session_name
        return result

    def set_active_window_title(self, window=None, custom_title=None):
        window_title = None
        if window is not None:
            window_title = self.get_window_title(window)
            if window_title is None:
                self.active_window_title = self.session_info.session_name
        elif custom_title is not None:
            window_title = custom_title
        else:
            self.active_window_title = window_title
        if self.prefs.deskbar["enabled"] == 1:
            self.deskbar.set_active_window_title(self.active_window_title)

    def update_active_window_title(self):
        if self.last_raised_window is not None:
            self.set_active_window_title(self.last_raised_window)

    def update_window_count(self):
        if self.deskbar is not None:
            self.deskbar.set_window_count(len(self.managed_windows))

    ### WINDOW CONTROLS

    def manage_window(self, window):
        attributes = self.get_window_attributes(window)
        if attributes is None:
            return
        if attributes.override_redirect:
            return
        if self.is_managed_window(window):
            return

        if self.prefs.dev["debug"] == 1:
            print("Found window: %s", self.get_window_shortname(window))

        # Initiate window stack
        window_stack = WindowStack(body=window)

        # Manage window
        self.managed_windows.append(window)
        self.exposed_windows.append(window)
        self.window_order = len(self.managed_windows) - 1
        self.update_window_count()

        window.map()
        mask = X.EnterWindowMask | X.LeaveWindowMask
        window.change_attributes(event_mask=mask)

        self.decorate_window(window_stack)

    def unmanage_window(self, window):
        if self.is_managed_window(window):
            if self.prefs.dev["debug"] == 1:
                print("Unmanaging window: %s", self.get_window_shortname(window))
            if window in self.managed_windows:
                self.managed_windows.remove(window)
                self.window_order = len(self.managed_windows) - 1
                self.update_window_count()
            if window in self.exposed_windows:
                self.exposed_windows.remove(window)

    def destroy_window(self, window):
        if self.is_dock(window) is False:
            if self.prefs.dev["debug"] == 1:
                print("Destroy window: %s", self.get_window_shortname(window))
            if self.is_managed_window(window):
                window.destroy()
                self.unmanage_window(window)

    def raise_window(self, window):
        if not self.is_dock(window):
            if not self.is_managed_window(window):
                return
            window.raise_window()
            self.last_raised_window = window
            self.set_active_window_title(window)
            if self.deskbar is not None:
                self.deskbar.update()

    def focus_window(self, window):
        if self.is_dock(window) or not self.is_managed_window(window) or not self.is_alive_window(window):
            return
        window.set_input_focus(X.RevertToParent, 0)
        self.set_focus_window_border(window)

    def cycle_windows(self):
        if len(self.managed_windows) > 0:
            self.window_order += 1
            if self.window_order > len(self.managed_windows) - 1:
                self.window_order = 0
            window = self.managed_windows[self.window_order]
            if self.is_cyclical_window(window) is False:
                if self.window_order >= len(self.managed_windows) - 1:
                    self.window_order = 0
                else:
                    self.window_order += 1
                window = self.managed_windows[self.window_order]
            self.focus_window(window)
            self.raise_window(window)
        else:
            self.window_order = -1

    ### WINDOW DECORATION

    def is_window_maximized(self, window):
        states = self.get_window_state(window)
        print(states)

    def move_window(self, xdiff, ydiff):
        window_dimensions = self.get_window_geometry(self.start.child)
        if self.deskbar is not None and ydiff < 0 and window_dimensions.y <= self.deskbar.real_height:
            y = self.deskbar.real_height
        else:
            y = self.attr.y + (self.start.detail == 1 and ydiff or 0)
        self.start.child.configure(
            x=self.attr.x + (self.start.detail == 1 and xdiff or 0),
            y=y,
            width=max(1, self.attr.width + (self.start.detail == 3 and xdiff or 0)),
            height=max(1, self.attr.height + (self.start.detail == 3 and ydiff or 0))
        )

    def resize_window(self, window, position):
        if self.is_dock(window) is False:
            if self.prefs.dev["debug"] == 1:
                print("Triggered window resize")
            if position in self.window_resize_options:
                window_x, window_y, window_width, window_height = None, None, None, None
                if position == "center":
                    window_dimensions = self.get_window_geometry(window)
                    window_width, window_height = window_dimensions.width, window_dimensions.height
                    window_x = (self.display_dimensions.width - window_width) // 2
                    window_y = (self.display_dimensions.height - window_height) // 2
                elif position == "maximize":
                    window_width, window_height, has_deskbar = self.get_maximum_available_geometry()
                    window_x = -self.prefs.appearance["window_border_width"]
                    window_y = -self.prefs.appearance["window_border_width"] if not has_deskbar else (
                            -self.prefs.appearance["window_border_width"] + self.deskbar.real_height
                    )
                elif position == "left" or position == "right":
                    window_width = self.display_dimensions.width // 2
                    window_height = self.display_dimensions.height + (
                        0 if self.deskbar is None else self.deskbar.height)
                    if position == "left":
                        window_x = -self.prefs.appearance["window_border_width"]
                    elif position == "right":
                        window_x = window_width - self.prefs.appearance["window_border_width"]
                    window_y = -self.prefs.appearance["window_border_width"] if self.deskbar is None else (
                            -self.prefs.appearance[
                                "window_border_width"] + self.deskbar.height + self.deskbar.border_width
                    )
                elif position == "top" or position == "bottom":
                    window_width = self.display_dimensions.width
                    window_height = (self.display_dimensions.height + (
                        0 if self.deskbar is None else self.deskbar.height)) // 2
                    if position == "top":
                        window_y = -self.prefs.appearance["window_border_width"]
                    elif position == "bottom":
                        window_y = window_height + self.prefs.appearance["window_border_width"]
                    window_x = -self.prefs.appearance["window_border_width"]

                if position == "maximize":
                    self.ewmh.setWmState(window, 1, "_NET_WM_STATE_MAXIMIZED_VERT")
                    self.ewmh.setWmState(window, 1, "_NET_WM_STATE_MAXIMIZED_HORIZ")
                else:
                    self.ewmh.setWmState(window, 0, "_NET_WM_STATE_MAXIMIZED_VERT")
                    self.ewmh.setWmState(window, 0, "_NET_WM_STATE_MAXIMIZED_HORIZ")

                window.configure(
                    x=window_x,
                    y=window_y,
                    width=window_width,
                    height=window_height
                )
            else:
                print("Invalid window position: " + position)

    def get_string_physical_width(self, text):
        font = self.dpy.open_font(FONT_NAME)
        result = font.query_text_extents(text.encode())
        return result.overall_width

    def decorate_window(self, window_stack):
        self.set_cursor(window_stack.body)
        if self.is_dock(window_stack.body) is False:
            body_dimensions = self.get_window_geometry(window_stack.body)
            body_width, body_height = body_dimensions.width, body_dimensions.height

            # Generate window_stack frame
            window_stack.frame = self.dpy_root.create_window(
                8, 8, body_width, body_height + 24, 1,
                self.screen.root_depth,
                background_pixel=self.pixel_palette.get_named_pixel("white")
            )
            window_stack.frame.map()
            window_stack.body.reparent(window_stack.frame, 0, 24)

            frame_dimensions = self.get_window_geometry(window_stack.frame)
            frame_width, frame_height = frame_dimensions.width, frame_dimensions.height
            frame_x = 5
            frame_y = 25

            # Generate window_stack titlebar
            window_stack.titlebar = self.dpy_root.create_window(
                0, 0, frame_width, 24, 0,
                self.screen.root_depth,
                background_pixel=self.pixel_palette.get_named_pixel(self.prefs.appearance["active_window_border_color"])
            )
            window_stack.titlebar.reparent(window_stack.frame, 0, 0)
            window_stack.titlebar.map()
            window_title = self.get_window_title(window_stack.body)
            window_title_length = self.get_string_physical_width(window_title)
            print(window_title + ": " + str(window_title_length))
            background_pixel = self.pixel_palette.get_named_pixel("black")
            foreground_pixel = self.pixel_palette.get_named_pixel("white")
            window_title_gc = self.dpy_root.create_gc(
                font=load_font(self.dpy, FONT_NAME),
                foreground=foreground_pixel,
                background=background_pixel,
            )
            window_stack.titlebar.draw_text(
                window_title_gc,
                0,
                0,
                window_title.text.encode('utf-8')
            )

            # Reposition window according to configuration
            if self.prefs.placement["auto_window_placement"] == 1:
                # Move new window out of the way of the deskbar
                if self.prefs.placement["auto_window_fit"] == 1:
                    # Resize window to fit the screen
                    if frame_width + frame_x >= self.display_dimensions.width:
                        frame_width -= frame_x * 2
                    if frame_height + frame_y >= self.display_dimensions.height:
                        frame_height -= frame_y * 2
                if self.prefs.placement["center_window_placement"] == 1:
                    frame_x = (self.display_dimensions.width - frame_width) // 2
                    frame_y = (self.display_dimensions.height - frame_height) // 2

            # Configure window_stack
            window_stack.frame.configure(
                x=frame_x,
                y=frame_y,
                width=frame_width,
                height=frame_height
            )
            window_stack.titlebar.configure(
                x=0,
                y=0,
                width=frame_width,
                height=24
            )
            window_stack.body.configure(
                x=0,
                y=24,
                width=frame_width,
                height=frame_height - 24
            )
            self.set_unfocus_window_border(window_stack.frame)

    def set_unfocus_window_border(self, window):
        if not self.is_dock(window):
            border_color = self.pixel_palette.get_named_pixel("lightgray")
            if self.prefs.appearance["inactive_window_border_color"] in self.pixel_palette.hex_map.keys():
                border_color = self.pixel_palette.get_named_pixel(self.prefs.appearance["inactive_window_border_color"])
            elif self.pixel_palette.is_color_hex(self.prefs.appearance["inactive_window_border_color"]) is True:
                border_color = self.pixel_palette.get_hex_pixel(self.prefs.appearance["inactive_window_border_color"])
            window.configure(border_width=self.prefs.appearance["window_border_width"])
            window.change_attributes(None, border_pixel=border_color)

    def set_focus_window_border(self, window):
        if not self.is_dock(window):
            border_color = self.pixel_palette.get_named_pixel("sienna")
            if self.prefs.appearance["active_window_border_color"] in self.pixel_palette.hex_map.keys():
                border_color = self.pixel_palette.get_named_pixel(self.prefs.appearance["active_window_border_color"])
            elif self.pixel_palette.is_color_hex(self.prefs.appearance["active_window_border_color"]) is True:
                border_color = self.pixel_palette.get_hex_pixel(self.prefs.appearance["active_window_border_color"])
            window.change_attributes(None, border_pixel=border_color)

    def set_cursor(self, window):
        font = self.dpy.open_font('cursor')
        cursor = font.create_glyph_cursor(
            font,
            Xcursorfont.left_ptr,
            Xcursorfont.left_ptr + 1,
            (65535, 65535, 65535),
            (0, 0, 0)
        )
        window.change_attributes(cursor=cursor)

    def set_background_color(self):
        background_color = self.pixel_palette.hex_map["slategray"]
        if self.pixel_palette.is_color_hex(self.prefs.appearance["background_color"]) is True:
            background_color = self.prefs.appearance["background_color"]
        elif self.prefs.appearance["background_color"] in self.pixel_palette.hex_map.keys():
            background_color = self.pixel_palette.hex_map[self.prefs.appearance["background_color"]]
        os.system('xsetroot -solid "' + background_color + '"')

    # EVENT HANDLING

    def keycode_to_string(self, detail):
        return XK.keysym_to_string(self.dpy.keycode_to_keysym(detail, 0))

    # From: https://stackoverflow.com/a/43880743
    def keycode_to_key(self, keycode, state):
        i = 0
        if state & X.ShiftMask:
            i += 1
        if state & X.Mod1Mask:
            i += 2
        return self.dpy.keycode_to_keysym(keycode, i)

    # From: https://stackoverflow.com/a/43880743
    def key_to_string(self, key):
        keys = []
        for name in dir(XK):
            if name.startswith("XK_") and getattr(XK, name) == key:
                keys.append(name.lstrip("XK_").replace("_L", "").replace("_R", ""))
        if keys:
            return " or ".join(keys)
        return "[%d]" % key

    # From: https://stackoverflow.com/a/43880743
    def keycode_to_string_mod(self, keycode, state):
        return self.key_to_string(self.keycode_to_key(keycode, state))

    def set_key_aliases(self):
        keystrings = [
            "x", "q",
            "minus", "equal", "bracketleft", "bracketright", "backslash", "slash",
            "F1", "Tab", "Escape", "space", "Return", "BackSpace"
        ]
        for keystring in keystrings:
            self.key_alias[keystring] = self.dpy.keysym_to_keycode(XK.string_to_keysym(keystring))

    def launcher_bindings(self, ev):
        if ev.detail == self.key_alias["Escape"]:
            self.deskbar.toggle_launcher(state=False)
        elif ev.detail == self.key_alias["BackSpace"] and len(self.deskbar.command_string) > 0:
            self.deskbar.command_string = self.deskbar.command_string[:-1]
            self.deskbar.update()
        elif ev.detail == self.key_alias["Return"]:
            run_command(self.deskbar.command_string)
            self.deskbar.toggle_launcher(state=False)
        else:
            key_string = self.keycode_to_string(ev.detail)
            if key_string:
                self.deskbar.command_string += key_string
                self.deskbar.update()

    def start_terminal(self):
        run_command('x-terminal-emulator')

    def start_launcher(self, ev):
        if self.deskbar is not None:
            self.deskbar.toggle_launcher(state=True)
            self.deskbar.command_string = ''
            self.deskbar.update()
            self.launcher_bindings(ev)
        else:
            self.start_terminal()

    def focus_raise(self, ev):
        self.focus_window(ev.window)
        self.raise_window(ev.window)

    def action_bindings(self, mapped_event_name, ev):
        try:
            if ev.child != X.NONE:
                window_event = {
                    "close": lambda: self.destroy_window(ev.child),
                    "maximize": lambda: self.resize_window(ev.child, "maximize"),
                    "move_center": lambda: self.resize_window(ev.child, "center"),
                    "move_left": lambda: self.resize_window(ev.child, "left"),
                    "move_right": lambda: self.resize_window(ev.child, "right"),
                    "move_top": lambda: self.resize_window(ev.child, "top"),
                    "move_bottom": lambda: self.resize_window(ev.child, "bottom"),
                    "focus": lambda: self.focus_raise(ev),
                }[mapped_event_name]
                window_event()
            session_event = {
                "terminal": self.start_terminal,
                "window_cycle": self.cycle_windows,
                "launcher": lambda: self.start_launcher(ev),
                "exit": self.end_session,
            }[mapped_event_name]
            session_event()
        except Exception as e:
            print(e)

    def on_key_press(self, ev):
        try:
            if ev.child != X.NONE:
                ev.child.send_event(ev)
        except Exception as e:
            print(e)

        key_string = self.keycode_to_string_mod(ev.detail, ev.state)
        if key_string:
            try:
                # ev.state == 24 for Alt
                # ev.state == 25 for Alt + Shift
                self.keys_down.add(key_string)
                print("Pressed: " + key_string + " - " + str(self.keys_down))
                mapped_event_name = list(key_combs.session.keys())[list(key_combs.session.values()).index(self.keys_down)]
                if self.deskbar is None or self.deskbar.launcher_is_running() is False:
                    self.action_bindings(mapped_event_name, ev)
            except Exception as e:
                print(e)
        if self.deskbar is not None and self.deskbar.launcher_is_running() is True:
            self.launcher_bindings(ev)

    def on_key_release(self, ev):
        key_string = self.keycode_to_string_mod(ev.detail, ev.state)
        if key_string:
            print(ev.state)
            try:
                self.keys_down.clear()
                self.dpy.ungrab_keyboard(X.CurrentTime)
                print("Released keys")
            except Exception as e:
                print(e)

    def event_handler(self):
        while 1:
            ev = self.dpy.next_event()
            if ev.type in [X.EnterNotify, X.LeaveNotify, X.MapNotify]:
                self.set_active_window_title(ev.window)

            if ev.type == X.KeyPress:
                self.on_key_press(ev)
            elif ev.type == X.KeyRelease:
                self.on_key_release(ev)
            elif ev.type == X.MapNotify:
                if self.is_cyclical_window(ev.window):
                    try:
                        self.manage_window(ev.window)
                        self.focus_window(ev.window)
                        self.raise_window(ev.window)
                    except AttributeError:
                        print("Unable to handle new window")
                        pass
            elif ev.type == X.DestroyNotify:
                try:
                    self.destroy_window(ev.window)
                except AttributeError:
                    print("Unable to unhandle new window")
                    pass
            elif ev.type == X.EnterNotify:
                self.focus_window(ev.window)
                if self.prefs.placement["auto_window_raise"] == 1:
                    self.raise_window(ev.window)
            elif ev.type == X.LeaveNotify:
                self.set_unfocus_window_border(ev.window)
            elif ev.type == X.ButtonPress and ev.child != X.NONE:
                if not self.is_dock(ev.child):
                    self.raise_window(ev.child)
                    self.set_focus_window_border(ev.child)
                    self.attr = ev.child.get_geometry()
                    self.start = ev
                elif self.deskbar is not None and ev.child == self.deskbar.deskbar:
                    if ev.detail == 1:
                        self.cycle_windows()
                    elif ev.detail == 3:
                        self.deskbar.toggle_window_count()
                        self.deskbar.update()
            elif ev.type == X.MotionNotify and self.start:
                xdiff = ev.root_x - self.start.root_x
                ydiff = ev.root_y - self.start.root_y
                self.move_window(xdiff, ydiff)
            elif ev.type == X.ButtonRelease:
                self.start = None
                self.attr = None
                if ev.child != X.NONE and self.is_dock(ev.child) is False:
                    self.ewmh.setWmState(ev.window, 0, "_NET_WM_STATE_MAXIMIZED_VERT")
                    self.ewmh.setWmState(ev.window, 0, "_NET_WM_STATE_MAXIMIZED_HORIZ")

            if self.display_corners is not None:
                self.display_corners.update()
            self.dpy.flush()

    # SESSION HANDLER

    def end_session(self):
        self.update_active_window_title_rt.stop()
        if self.prefs.deskbar["enabled"] == 1:
            self.deskbar.stop_repeated_events()
        if self.prefs.xround["enabled"] == 1:
            self.display_corners.stop()
        self.dpy.close()
        sys.exit(0)

    def main(self):
        # Register keyboard and mouse events
        self.dpy_root.grab_key(
            X.AnyKey,
            X.AnyModifier,
            1,
            X.GrabModeAsync,
            X.GrabModeAsync
        )
        self.dpy_root.grab_button(
            1,
            X.Mod1Mask | X.Mod2Mask,
            1,
            X.ButtonPressMask | X.ButtonReleaseMask | X.PointerMotionMask,
            X.GrabModeAsync,
            X.GrabModeAsync,
            X.NONE,
            X.NONE
        )
        self.dpy_root.grab_button(
            3,
            X.Mod1Mask | X.Mod2Mask,
            1,
            X.ButtonPressMask | X.ButtonReleaseMask | X.PointerMotionMask,
            X.GrabModeAsync,
            X.GrabModeAsync,
            X.NONE,
            X.NONE
        )
        self.dpy_root.change_attributes(event_mask=X.SubstructureNotifyMask)

        self.set_background_color()

        children = self.window_list()
        for child in children:
            if child.get_attributes().map_state:
                self.manage_window(child)

        # Draw deskbar
        if self.prefs.deskbar["enabled"] == 1:
            self.deskbar = Deskbar(
                self.ewmh, self.dpy, self.dpy_root, self.screen, self.display_dimensions,
                self.wm_window_type, self.wm_window_types,
                self.wm_state, self.wm_window_status,
                self.prefs, self.session_info
            )
            self.deskbar.draw()

        # Draw display corners
        if self.prefs.xround["enabled"] == 1:
            self.display_corners = DisplayCorners(
                self.ewmh, self.dpy, self.dpy_root, self.screen, self.display_dimensions,
                self.wm_window_type, self.wm_window_types,
                self.wm_state, self.wm_window_status
            )
            self.display_corners.draw()

        try:
            self.event_handler()
        except KeyboardInterrupt or error.ConnectionClosedError:
            self.end_session()
            sys.exit(0)

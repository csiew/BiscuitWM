# requires python-xlib

import os
import sys
import subprocess
from threading import Timer
from Xlib.display import Display
from Xlib import X, XK, Xatom, Xcursorfont, display, error

## CONSTANTS

PNT_OFFSET = 16


class SessionInfo(object):
    def __init__(self):
        self.session_name = "BiscuitWM"
        self.kernel_version = os.popen('uname -rm').read()[:-1]


'''
Thanks to MestreLion for their RepeatedTimer implementation
https://stackoverflow.com/a/13151299
- Standard library only, no external dependencies
- start() and stop() are safe to call multiple times even if the timer has already started/stopped
- function to be called can have positional and named arguments
- You can change interval anytime, it will be effective after next run. Same for args, kwargs and even function!
'''
class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


class DeskbarItem(object):
    def __init__(self, name, text="", width=0, interval=None, function=None):
        self.name = name
        self.text = text
        self.width = 0
        self.interval = interval
        self.function = function
        if interval is not None and function is not None:
            self.rt_event = RepeatedTimer(interval, function)
        else:
            self.rt_event = None

    def set_rt_event(self, interval, function):
        self.interval = interval
        self.function = function
        self.rt_event = RepeatedTimer(interval, function)

    def unset_rt_event(self):
        if self.rt_event is not None:
            self.rt_event.stop()
            self.rt_event = None
            self.interval = None
            self.function = None

    def start(self):
        if self.rt_event is not None:
            self.rt_event.start()

    def stop(self):
        if self.rt_event is not None:
            self.rt_event.stop()


class Deskbar(object):
    def __init__(
            self, dpy, dpy_root, screen, display_dimensions,
            wm_window_type, wm_window_type_dock
    ):
        self.dpy = dpy
        self.dpy_root = dpy_root
        self.screen = screen
        self.display_dimensions = display_dimensions
        self.wm_window_type = wm_window_type
        self.wm_window_type_dock = wm_window_type_dock

        self.border_width = 1
        self.height = 20
        self.text_y_alignment = 15
        self.padding_leading = 10
        self.padding_trailing = 15
        self.padding_between = 10

        self.refresh_rate = 5

        self.deskbar = None
        self.deskbar_gc = None

        self.deskbar_items = {
            "active_window_title": DeskbarItem("Window Title", text="BiscuitWM"),
            "memory_usage": DeskbarItem("Memory Usage", interval=10, function=self.set_memory_usage),
            "timestamp": DeskbarItem("Time", interval=1, function=self.set_timestamp)
        }
        self.deskbar_update_rt = RepeatedTimer(1, self.update)

    def set_active_window_title(self, window_title):
        self.deskbar_items["active_window_title"].text = window_title
        self.deskbar_items["active_window_title"].width = self.get_string_physical_width(window_title)

    def set_memory_usage(self):
        self.deskbar_items["memory_usage"].text = self.get_memory_usage() + "%"
        self.deskbar_items["memory_usage"].width = self.get_string_physical_width(self.deskbar_items["memory_usage"].text)

    def set_timestamp(self):
        self.deskbar_items["timestamp"].text = self.get_current_time()
        self.deskbar_items["timestamp"].width = self.get_string_physical_width(self.deskbar_items["timestamp"].text)

    def get_string_physical_width(self, text):
        font = self.dpy.open_font('9x15')
        result = font.query_text_extents(text.encode())
        return result.overall_width

    def get_memory_usage(self):
        return os.popen("free -m | awk 'NR==2{printf $3*100/$2}'").read()[:-1]

    def get_current_time(self):
        return os.popen('date +"%I:%M:%S %P"').read()[:-1]

    def start_repeated_events(self):
        for item in self.deskbar_items.values():
            item.start()
        self.deskbar_update_rt.start()

    def stop_repeated_events(self):
        for item in self.deskbar_items.values():
            item.stop()
        self.deskbar_update_rt.stop()

    def draw(self):
        screen_width, screen_height = self.display_dimensions.width, self.display_dimensions.height
        self.deskbar = self.dpy_root.create_window(
            -1, -1, screen_width, self.height, 1,
            self.screen.root_depth,
            background_pixel=self.screen.white_pixel,
            event_mask=X.ExposureMask | X.KeyPressMask | X.ButtonPressMask,
        )
        self.deskbar.change_property(self.wm_window_type, Xatom.ATOM, 32, [self.wm_window_type_dock], X.PropModeReplace)
        self.deskbar_gc = self.deskbar.create_gc(
            foreground=self.screen.black_pixel,
            background=self.screen.white_pixel,
        )
        self.deskbar.map()              # Draw deskbar
        self.set_timestamp()            # Set initial timestamp
        self.set_memory_usage()         # Set initial memory usage percentage
        self.update()                   # Initial update
        self.start_repeated_events()    # Start deskbar updates

    def update(self):
        self.deskbar.raise_window()
        self.deskbar.clear_area()

        # Leading items
        self.deskbar.draw_text(
            self.deskbar_gc,
            self.padding_leading,
            self.text_y_alignment,
            self.deskbar_items["active_window_title"].text.encode('utf-8')
        )

        # Trailing items
        self.deskbar.draw_text(
            self.deskbar_gc,
            self.display_dimensions.width - (
                    (self.deskbar_items["memory_usage"].width
                     + self.deskbar_items["timestamp"].width)
                    - (self.padding_between + self.padding_trailing)
            ),
            self.text_y_alignment,
            self.deskbar_items["memory_usage"].text.encode('utf-8')
        )
        self.deskbar.draw_text(
            self.deskbar_gc,
            self.display_dimensions.width-(self.deskbar_items["timestamp"].width-self.padding_trailing),
            self.text_y_alignment,
            self.deskbar_items["timestamp"].text.encode('utf-8')
        )


class Preferences(object):
    def __init__(
            self,
            DEBUG=True,
            AUTO_WINDOW_PLACE=True,
            AUTO_WINDOW_FIT=True,
            AUTO_WINDOW_RAISE=True,
            CENTER_WINDOW_PLACEMENT=True,
            DRAW_DESKBAR=True,
            WINDOW_BORDER_WIDTH=2,
            ACTIVE_WINDOW_BORDER_COLOR="#ff0000",
            INACTIVE_WINDOW_BORDER_COLOR="#000000"
        ):
        self.DEBUG = DEBUG
        self.AUTO_WINDOW_PLACE = AUTO_WINDOW_PLACE
        self.AUTO_WINDOW_FIT = AUTO_WINDOW_FIT
        self.AUTO_WINDOW_RAISE = AUTO_WINDOW_RAISE
        self.CENTER_WINDOW_PLACEMENT = CENTER_WINDOW_PLACEMENT
        self.DRAW_DESKBAR = DRAW_DESKBAR
        self.WINDOW_BORDER_WIDTH = WINDOW_BORDER_WIDTH
        self.ACTIVE_WINDOW_BORDER_COLOR = ACTIVE_WINDOW_BORDER_COLOR
        self.INACTIVE_WINDOW_BORDER_COLOR = INACTIVE_WINDOW_BORDER_COLOR


class WindowManager(object):
    def __init__(self, prefs, session_info):
        self.prefs = prefs
        self.session_info = session_info
        self.dpy = Display()
        self.screen = self.dpy.screen()
        self.dpy_root = self.screen.root
        self.dpy_protocol = display.Display()
        self.colormap = self.screen.default_colormap

        self.display_dimensions = self.get_display_geometry()

        self.managed_windows = []
        self.exposed_windows = []
        self.last_raised_window = None
        self.active_window_title = self.session_info.session_name
        self.window_order = -1

        self.key_alias = {}

        self.start = None
        self.attr = None

        self.wm_window_type = self.dpy.intern_atom('_NET_WM_WINDOW_TYPE')
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
            "above": self.dpy.intern_atom('_NET_WM_STATE_ABOVE')
        }

        self.wm_window_cyclical = [
            self.wm_window_types["normal"],
            self.wm_window_types["dialog"],
            self.wm_window_types["utility"],
            self.wm_window_types["toolbar"],
            self.wm_window_types["menu"],
            self.wm_window_types["splash"]
        ]

        self.deskbar = Deskbar(
            self.dpy, self.dpy_root, self.screen, self.display_dimensions,
            self.wm_window_type, self.wm_window_types["dock"]
        )

        self.set_cursor(self.dpy_root)

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
        except error.BadWindow:
            print("Failed to detect if window is dock")
            pass
        if result is not None and result.value[0] == self.wm_window_types["dock"]:
            return True
        return False

    def is_popup_window(self, window):
        result = None
        try:
            result = window.get_full_property(self.wm_window_type, Xatom.ATOM)
        except error.BadWindow:
            print("Failed to detect if window is dock")
            pass
        if result is not None and (result.value[0] == self.wm_window_types["menu"] or result.value[0] == self.wm_window_types["splash"]):
            return True
        return False

    def is_cyclical_window(self, window):
        result = None
        try:
            result = window.get_full_property(self.wm_window_type, Xatom.ATOM)
        except error.BadWindow:
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

    def get_window_attributes(self, window):
        try:
            return window.get_attributes()
        except:
            return None

    def get_window_shortname(self, window):
        return '0x{:x} [{}]'.format(window.id, self.get_window_class(window))

    def get_window_title(self, window):
        result = None
        try:
            result = window.get_wm_icon_name()
        except:
            pass
        if result is None:
            return "BiscuitWM"
        return result

    def set_active_window_title(self, window):
        window_title = self.get_window_title(window)
        if window_title is None:
            self.active_window_title = self.session_info.session_name
        else:
            self.active_window_title = window_title
        if self.prefs.DRAW_DESKBAR is True:
            self.deskbar.set_active_window_title(self.active_window_title)

    ### WINDOW CONTROLS

    def manage_window(self, window):
        """Bring all existing windows into window manager's control."""
        attributes = self.get_window_attributes(window)
        if attributes is None:
            return
        if attributes.override_redirect:
            return
        if self.is_managed_window(window):
            return

        if self.prefs.DEBUG is True:
            print("Found window: %s", self.get_window_shortname(window))
        self.managed_windows.append(window)
        self.exposed_windows.append(window)
        self.window_order = len(self.managed_windows)-1

        window.map()
        mask = X.EnterWindowMask | X.LeaveWindowMask
        window.change_attributes(event_mask=mask)

        self.decorate_window(window)

    def unmanage_window(self, window):
        if self.is_managed_window(window):
            if self.prefs.DEBUG is True:
                print("Unmanaging window: %s", self.get_window_shortname(window))
            if window in self.managed_windows:
                self.managed_windows.remove(window)
                self.window_order = len(self.managed_windows)-1
            if window in self.exposed_windows:
                self.exposed_windows.remove(window)

    def destroy_window(self, window):
        if self.prefs.DEBUG is True:
            print("Destroy window: %s", self.get_window_shortname(window))
        if self.is_managed_window(window):
            window.destroy()
            self.unmanage_window(window)

    def raise_window(self, window):
        if not self.is_dock(window):
            if not self.is_managed_window(window):
                return
            window.configure(stack_mode=X.Above)
            self.last_raised_window = window
            self.set_active_window_title(window)

    def focus_window(self, window):
        if self.is_dock(window) or not self.is_managed_window(window) or not self.is_alive_window(window):
            return
        window.set_input_focus(X.RevertToParent, 0)
        self.set_focus_window_border(window)

    def cycle_windows(self):
        if len(self.managed_windows) > 0:
            self.window_order += 1
            if self.window_order > len(self.managed_windows)-1:
                self.window_order = 0
            window = self.managed_windows[self.window_order]
            if self.is_cyclical_window(window) is False:
                if self.window_order >= len(self.managed_windows)-1:
                    self.window_order = 0
                else:
                    self.window_order += 1
                window = self.managed_windows[self.window_order]
            self.focus_window(window)
            self.raise_window(window)
        else:
            self.window_order = -1

    ### WINDOW DECORATION

    def decorate_window(self, window):
        self.set_cursor(window)
        window_dimensions = self.get_window_geometry(window)
        window_width, window_height = window_dimensions.width, window_dimensions.height
        window_x = 5
        window_y = 25
        if self.is_dock(window) is False:
            if self.prefs.AUTO_WINDOW_PLACE is True:
                # Move new window out of the way of the deskbar
                if self.prefs.AUTO_WINDOW_FIT is True:
                    # Resize window to fit the screen
                    if window_dimensions.width+window_x >= self.display_dimensions.width:
                        window_width -= window_x*2
                    if window_dimensions.height+window_y >= self.display_dimensions.height:
                        window_height -= window_y*2
                if self.prefs.CENTER_WINDOW_PLACEMENT is True:
                    window_x = (self.display_dimensions.width - window_width)//2
                    window_y = (self.display_dimensions.height - window_height)//2
                window.configure(
                    x=window_x,
                    y=window_y,
                    width=window_width,
                    height=window_height
                )
                self.set_unfocus_window_border(window)

    def set_unfocus_window_border(self, window):
        if not self.is_dock(window):
            border_color = self.colormap.alloc_named_color(self.prefs.INACTIVE_WINDOW_BORDER_COLOR).pixel
            window.configure(border_width=self.prefs.WINDOW_BORDER_WIDTH)
            window.change_attributes(None, border_pixel=border_color)

    def set_focus_window_border(self, window):
        if not self.is_dock(window):
            border_color = self.colormap.alloc_named_color(self.prefs.ACTIVE_WINDOW_BORDER_COLOR).pixel
            window.configure(border_width=self.prefs.WINDOW_BORDER_WIDTH)
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

    def draw_window_titlebar(self, window):
        window_dimensions = self.get_window_geometry(window)
        window_width, window_height = window_dimensions.width, window_dimensions.height
        window_x, window_y = window_dimensions.x, window_dimensions.y
        window_titlebar = self.dpy_root.create_window(
            window_x, window_y, window_width, 20, 1,
            self.screen.root_depth,
            background_pixel=self.screen.white_pixel,
            event_mask=X.ExposureMask | X.KeyPressMask | X.ButtonPressMask,
        )
        window_titlebar_gc = window_titlebar.create_gc(
            foreground=self.screen.black_pixel,
            background=self.screen.white_pixel,
        )
        window_titlebar.map()
        window_titlebar.draw_text(window_titlebar_gc, 5, 15, self.get_window_title(window).encode('utf-8'))

    # DEBUG

    def print_event_type(self, ev):
        event = ev.type
        msg = "Unknown"
        if event == X.CreateNotify:
            msg = "CreateNotify"
        elif event == X.DestroyNotify:
            msg = "DestroyNotify"
        elif event == X.MapNotify:
            msg = "MapNotify"
        elif event == X.Expose:
            msg = "Expose"
        elif event == X.FocusIn:
            msg = "FocusIn"
        elif event == X.FocusOut:
            msg = "FocusIn"
        elif event == X.EnterNotify:
            msg = "EnterNotify"
        elif event == X.LeaveNotify:
            msg = "LeaveNotify"
        elif event == X.MotionNotify:
            msg = "MotionNotify"
        elif event == X.KeyPress:
            msg = "KeyPress"
        elif event == X.ButtonPress:
            msg = "ButtonPress"
        print(msg + " event")

    # SPECIAL

    def start_terminal(self):
        subprocess.Popen('x-terminal-emulator')

    # EVENT HANDLING

    def set_key_aliases(self):
        self.key_alias["x"] = self.dpy.keysym_to_keycode(XK.string_to_keysym("x"))
        self.key_alias["q"] = self.dpy.keysym_to_keycode(XK.string_to_keysym("q"))
        self.key_alias["F1"] = self.dpy.keysym_to_keycode(XK.string_to_keysym("F1"))
        self.key_alias["Tab"] = self.dpy.keysym_to_keycode(XK.XK_Tab)
        self.key_alias["Escape"] = self.dpy.keysym_to_keycode(XK.XK_Escape)

    def handle_keypress(self, ev):
        if ev.detail in self.key_alias.values():
            print("Key is aliased")
            if ev.detail == self.key_alias["x"]:
                self.start_terminal()
            elif ev.detail == self.key_alias["q"] and ev.child != X.NONE:
                self.destroy_window(ev.child)
            elif ev.detail == self.key_alias["F1"] and ev.child != X.NONE:
                self.focus_window(ev.window)
                self.raise_window(ev.window)
            elif ev.detail == self.key_alias["Tab"]:
                self.cycle_windows()
            elif ev.detail == self.key_alias["Escape"]:
                self.end_session()
        else:
            print("Key is not aliased")

    def loop(self):
        while 1:
            ev = self.dpy.next_event()
            if self.prefs.DEBUG is True:
                self.print_event_type(ev)

            if ev.type in [X.EnterNotify, X.LeaveNotify, X.MapNotify]:
                self.set_active_window_title(ev.window)

            if ev.type == X.MapNotify:
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
                if self.prefs.AUTO_WINDOW_RAISE is True:
                    self.raise_window(ev.window)
            elif ev.type == X.LeaveNotify:
                self.set_unfocus_window_border(ev.window)
            elif ev.type == X.KeyPress:
                self.handle_keypress(ev)
            elif ev.type == X.ButtonPress and ev.child != X.NONE:
                self.raise_window(ev.child)
                self.attr = ev.child.get_geometry()
                self.start = ev
            elif ev.type == X.MotionNotify and self.start:
                xdiff = ev.root_x - self.start.root_x
                ydiff = ev.root_y - self.start.root_y
                if not self.is_dock(self.start.child):
                    self.start.child.configure(
                        x = self.attr.x + (self.start.detail == 1 and xdiff or 0),
                        y = self.attr.y + (self.start.detail == 1 and ydiff or 0),
                        width = max(1, self.attr.width + (self.start.detail == 3 and xdiff or 0)),
                        height = max(1, self.attr.height + (self.start.detail == 3 and ydiff or 0))
                    )
            elif ev.type == X.ButtonRelease:
                self.start = None
                self.attr = None

            self.dpy.flush()
    
    def main(self):
        # Register keyboard and mouse events
        self.set_key_aliases()
        self.dpy_root.grab_key(
            X.AnyKey,
            X.Mod1Mask,
            1,
            X.GrabModeAsync,
            X.GrabModeAsync
        )
        self.dpy_root.grab_button(
            1,
            X.Mod1Mask,
            1,
            X.ButtonPressMask | X.ButtonReleaseMask | X.PointerMotionMask,
            X.GrabModeAsync,
            X.GrabModeAsync,
            X.NONE,
            X.NONE
        )
        self.dpy_root.grab_button(
            3,
            X.Mod1Mask,
            1,
            X.ButtonPressMask | X.ButtonReleaseMask | X.PointerMotionMask,
            X.GrabModeAsync,
            X.GrabModeAsync,
            X.NONE,
            X.NONE
        )
        self.dpy_root.change_attributes(event_mask=X.SubstructureNotifyMask)

        children = self.window_list()
        for child in children:
            if child.get_attributes().map_state:
                self.manage_window(child)

        # Draw deskbar
        if self.prefs.DRAW_DESKBAR is True:
            self.deskbar.draw()

        try:
            self.loop()
        except KeyboardInterrupt or error.ConnectionClosedError:
            sys.exit(0)

    def end_session(self):
        self.deskbar.stop_repeated_events()
        self.dpy.close()
        sys.exit(0)


if __name__ == "__main__":
    WindowManager(prefs=Preferences(), session_info=SessionInfo()).main()

# requires python-xlib

import os
import sys
import subprocess
from Xlib.display import Display
from Xlib import X, XK, Xatom, Xcursorfont, error

## CONSTANTS

PNT_OFFSET = 16


class SessionInfo:
    def __init__(self):
        self.session_name = "BiscuitWM".encode('utf-8')
        self.kernel_version = os.popen('uname -rm').read()[:-1].encode('utf-8')


class Preferences:
    def __init__(
            self,
            DEBUG=True,
            AUTO_WINDOW_PLACE=True,
            AUTO_WINDOW_FIT=True,
            AUTO_WINDOW_RAISE=True,
            DRAW_DESKBAR=True,
            WINDOW_BORDER_WIDTH=2,
            ACTIVE_WINDOW_BORDER_COLOR="#ff0000",
            INACTIVE_WINDOW_BORDER_COLOR="#000000"
        ):
        self.DEBUG = DEBUG
        self.AUTO_WINDOW_PLACE = AUTO_WINDOW_PLACE
        self.AUTO_WINDOW_FIT = AUTO_WINDOW_FIT
        self.AUTO_WINDOW_RAISE = AUTO_WINDOW_RAISE
        self.DRAW_DESKBAR = DRAW_DESKBAR
        self.WINDOW_BORDER_WIDTH = WINDOW_BORDER_WIDTH
        self.ACTIVE_WINDOW_BORDER_COLOR = ACTIVE_WINDOW_BORDER_COLOR
        self.INACTIVE_WINDOW_BORDER_COLOR = INACTIVE_WINDOW_BORDER_COLOR


class Session:
    def __init__(self, prefs, session_info):
        self.prefs = prefs
        self.session_info = session_info
        self.dpy = Display()
        self.screen = self.dpy.screen()
        self.dpy_root = self.screen.root
        self.colormap = self.screen.default_colormap

        self.managed_windows = []
        self.exposed_windows = []
        self.last_raised_window = None

        self.key_alias = {}

        self.start = None
        self.attr = None

        self.wm_window_type = self.dpy.intern_atom('_NET_WM_WINDOW_TYPE')
        self.wm_window_type_dock = self.dpy.intern_atom('_NET_WM_WINDOW_TYPE_DOCK')
        self.wm_window_type_menu = self.dpy.intern_atom('_NET_WM_WINDOW_TYPE_MENU')
        self.wm_window_type_splash = self.dpy.intern_atom('_NET_WM_WINDOW_TYPE_SPLASH')
        self.wm_window_type_active = self.dpy.intern_atom('_NET_ACTIVE_WINDOW')

        self.deskbar = None
        self.deskbar_gc = None

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
        if result is not None and result.value[0] == self.wm_window_type_dock:
            return True
        return False

    def is_popup_window(self, window):
        result = None
        try:
            result = window.get_full_property(self.wm_window_type, Xatom.ATOM)
        except error.BadWindow:
            print("Failed to detect if window is dock")
            pass
        if result is not None and (result.value[0] == self.wm_window_type_menu or result.value[0] == self.wm_window_type_splash):
            return True
        return False

    def is_active(self, atom):
        if atom == self.wm_window_type_active:
            return True
        return False

    def get_active_window(self):
        window = None
        try:
            window = self.dpy_root.get_full_property(self.wm_window_type_active, Xatom.ATOM)
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
        try:
            return window.get_wm_icon_name()
        except:
            return "BiscuitWM"

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

    def focus_window(self, window):
        if not self.is_managed_window(window):
            return

        if not self.is_alive_window(window):
            return

        window.set_input_focus(X.RevertToParent, 0)
        self.set_focus_window_border(window)

    ### WINDOW DECORATION

    def decorate_window(self, window):
        self.set_cursor(window)
        window_x = 5
        window_y = 25
        window_dimensions = self.get_window_geometry(window)
        window_width = window_dimensions.width
        window_height = window_dimensions.height
        display_dimensions = self.get_display_geometry()
        if self.is_dock(window) is False:
            if self.prefs.AUTO_WINDOW_PLACE is True:
                # Move new window out of the way of the deskbar
                if self.prefs.AUTO_WINDOW_FIT is True:
                    # Resize window to fit the screen
                    if window_dimensions.width+window_x >= display_dimensions.width:
                        window_width -= window_x*2
                    if window_dimensions.height+window_y >= display_dimensions.height:
                        window_height -= window_y*2
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

    def draw_deskbar(self):
        screen_dimensions = self.get_display_geometry()
        screen_width, screen_height = screen_dimensions.width, screen_dimensions.height
        self.deskbar = self.dpy_root.create_window(
            -1, -1, screen_width, 20, 1,
            self.screen.root_depth,
            background_pixel=self.screen.white_pixel,
            event_mask=X.ExposureMask | X.KeyPressMask | X.ButtonPressMask,
        )
        self.deskbar.change_property(self.wm_window_type, Xatom.ATOM, 32, [self.wm_window_type_dock, ], X.PropModeReplace)
        self.deskbar_gc = self.deskbar.create_gc(
            foreground=self.screen.black_pixel,
            background=self.screen.white_pixel,
        )
        self.deskbar.map()
        self.draw_deskbar_content()
        print(self.deskbar.get_full_property(self.wm_window_type, Xatom.ATOM).value[0])
        print(self.wm_window_type_dock)

    def draw_deskbar_content(self):
        self.deskbar.raise_window()
        self.deskbar.clear_area()
        '''
        self.deskbar.fill_rectangle(self.deskbar_gc, 5, 5, 10, 10)
        self.deskbar.draw_text(self.deskbar_gc, 20, 15, self.session_info.session_name)
        self.deskbar.draw_text(self.deskbar_gc, 80, 15, self.session_info.kernel_version)
        '''
        if self.last_raised_window is None:
            self.deskbar.draw_text(self.deskbar_gc, 5, 15, self.session_info.session_name)
        else:
            active_window_title = self.get_window_title(self.last_raised_window)
            print("Active window: %s", active_window_title)
            self.deskbar.draw_text(self.deskbar_gc, 5, 15, active_window_title.encode('utf-8'))

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

    def handle_keypress(self, ev):
        if ev.detail in self.key_alias.values():
            print("Key is aliased")
            if ev.detail == self.key_alias["x"]:
                self.start_terminal()
            elif ev.detail == self.key_alias["q"] and ev.child != X.NONE:
                self.destroy_window(ev.child)
            elif ev.detail == self.key_alias["F1"] and ev.child != X.NONE:
                self.raise_window(ev.window)
        else:
            print("Key is not aliased")

    def loop(self):
        while 1:
            ev = self.dpy.next_event()
            if self.prefs.DEBUG is True:
                self.print_event_type(ev)

            if ev.type == X.CreateNotify:
                try:
                    self.manage_window(ev.window)
                    if not self.is_popup_window(ev.window):
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

            self.draw_deskbar_content()
            self.dpy.sync()

    def set_key_aliases(self):
        self.key_alias["x"] = self.dpy.keysym_to_keycode(XK.string_to_keysym("x"))
        self.key_alias["q"] = self.dpy.keysym_to_keycode(XK.string_to_keysym("q"))
        self.key_alias["F1"] = self.dpy.keysym_to_keycode(XK.string_to_keysym("F1"))
    
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

        # Draw deskbar
        if self.prefs.DRAW_DESKBAR is True:
            self.draw_deskbar()
            self.draw_deskbar_content()

        children = self.window_list()
        for child in children:
            if child.get_attributes().map_state:
                self.manage_window(child)

        # Event loop
        try:
            self.loop()
        except KeyboardInterrupt:
            sys.exit(0)


if __name__ == "__main__":
    session_info = SessionInfo()
    prefs = Preferences()
    session = Session(prefs=prefs, session_info=session_info)
    session.main()


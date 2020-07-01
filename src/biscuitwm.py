# requires python-xlib

import os
import sys
from Xlib.display import Display
from Xlib import X, XK, Xatom, Xcursorfont


PNT_OFFSET = 16

AUTO_WINDOW_PLACE = True
AUTO_WINDOW_FIT = True
DRAW_DESKBAR = True


class SessionInfo:
    def __init__(self):
        self.session_name = "BiscuitWM"
        self.kernel_version = os.popen('uname -rm').read()[:-1]


class Session:
    def __init__(self, session_info):
        self.session_info = session_info
        self.dpy = Display()
        self.screen = self.dpy.screen()
        self.dpy_root = self.screen.root
        self.colormap = self.screen.default_colormap

        self.managed_windows = []
        self.exposed_windows = []
        self.last_raised_window = None

        self.key_handlers = {}

        self.start = None
        self.attr = None

        self.wm_window_type = self.dpy.intern_atom('_NET_WM_WINDOW_TYPE')
        self.wm_window_type_dock = self.dpy.intern_atom('_NET_WM_WINDOW_TYPE_DOCK')
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
        result = window.get_full_property(self.wm_window_type, Xatom.ATOM)
        if result is not None and result.value[0] == self.wm_window_type_dock:
            return True
        return False

    def is_active(self, atom):
        if atom == self.wm_window_type_active:
            return True
        return False

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

        print("Found window: %s", self.get_window_shortname(window))
        self.managed_windows.append(window)
        self.exposed_windows.append(window)

        window.map()
        mask = X.EnterWindowMask | X.LeaveWindowMask
        window.change_attributes(event_mask=mask)

        self.decorate_window(window)

    def unmanage_window(self, window):
        if self.is_managed_window(window):
            print("Unmanaging window: %s", self.get_window_shortname(window))
            if window in self.managed_windows:
                self.managed_windows.remove(window)
            if window in self.exposed_windows:
                self.exposed_windows.remove(window)

    def destroy_window(self, window):
        print("Destroy window: %s", self.get_window_shortname(window))
        if self.is_managed_window(window):
            window.destroy()
            self.unmanage_window(window)

    def raise_window(self, window):
        if not self.is_managed_window(window):
            return
        window.configure(stack_mode=X.Above)
        self.last_raised_window = window
        self.set_focus_window_border(window)

    def lower_window(self, window):
        if not self.is_managed_window(window):
            return
        window.configure(stack_mode=X.Below)
        if self.last_raised_window == window:
            self.last_raised_window = None

    def raise_or_lower_window(self, window):
        if self.last_raised_window == window:
            self.lower_window(window)
        else:
            self.raise_window(window)

    def focus_window(self, window):
        if not self.is_managed_window(window):
            return

        if not self.is_alive_window(window):
            return

        window.set_input_focus(X.RevertToParent, 0)
        self.set_focus_window_border(window)

    def focus_next_window(self, window=None):
        def _sort_key(window):
            geom = self.get_window_geometry(window)
            if geom is None:
                return 1000000000
            else:
                return geom.x * 10000 + geom.y

        windows = sorted(self.exposed_windows, key=_sort_key)
        try:
            i = windows.index(window)
            next_window = windows[(i+1) & len(windows)]
        except ValueError:
            if windows:
                next_window = windows[0]
            else:
                return
        next_window.raise_window()
        next_window.warp_pointer(PNT_OFFSET, PNT_OFFSET)
        self.focus_window(next_window)

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
            if AUTO_WINDOW_PLACE is True:
                # Move new window out of the way of the deskbar
                if AUTO_WINDOW_FIT is True:
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
        border_color = self.colormap.alloc_named_color(\
            "#000000").pixel
        window.configure(border_width=1)
        window.change_attributes(None, border_pixel=border_color)

    def set_focus_window_border(self, window):
        if not self.is_dock(window):
            border_color = self.colormap.alloc_named_color(\
                "#ff0000").pixel
            window.configure(border_width=1)
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
        self.raise_window(self.deskbar)
        self.deskbar.fill_rectangle(self.deskbar_gc, 5, 5, 10, 10)
        self.deskbar.draw_text(self.deskbar_gc, 20, 15, self.session_info.session_name)
        self.deskbar.draw_text(self.deskbar_gc, 120, 15, self.session_info.kernel_version)

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

    def loop(self):
        while 1:
            ev = self.dpy.next_event()
            self.print_event_type(ev)

            if ev.type == X.CreateNotify:
                try:
                    self.manage_window(ev.window)
                except AttributeError:
                    print("Unable to handle new window")
                    pass
            elif ev.type == X.DestroyNotify:
                try:
                    self.unmanage_window(ev.window)
                except AttributeError:
                    print("Unable to unhandle new window")
                    pass
            elif ev.type == X.EnterNotify:
                self.raise_window(ev.window)
            elif ev.type == X.LeaveNotify:
                self.set_unfocus_window_border(ev.window)
            elif ev.type == X.KeyPress and ev.child != X.NONE:
                self.raise_window(ev.child)
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
            self.dpy.flush()
    
    def main(self):
        # Register keyboard and mouse events
        self.dpy_root.grab_key(
            self.dpy.keysym_to_keycode(XK.string_to_keysym("F1")),
            X.Mod1Mask | X.Mod2Mask,
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

        # Draw deskbar
        if DRAW_DESKBAR is True:
            self.draw_deskbar()

        children = self.window_list()
        for child in children:
            if child.get_attributes().map_state:
                self.manage_window(child)
            '''
            window = self.managed_windows[-1]
            self.focus_window(window)
            '''

        # Event loop
        try:
            self.loop()
        except KeyboardInterrupt:
            sys.exit(0)


if __name__ == "__main__":
    session_info = SessionInfo()
    session = Session(session_info=session_info)
    session.main()


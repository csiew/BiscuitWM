# requires python-xlib

import os
import sys
from Xlib.display import Display
from Xlib import X, XK, Xatom, Xcursorfont


PNT_OFFSET = 16


AUTO_WINDOW_PLACE = True
DRAW_DESKBAR = True

EVENT_HANDLER = {
    X.KeyPress: 'handle_keypress',
}

KEYBOARD_HANDLER = {
    'Tab':
    {'modifier': X.Mod1Mask | X.Mod2Mask, 'method': 'cb_focus_next_window'},
    'm': {
        'modifier': X.Mod1Mask | X.Mod2Mask, 'method':
        'cb_raise_or_lower_window'
    },
    '1': {
        'modifier': X.Mod1Mask | X.Mod2Mask, 'command':
        'pidof xterm || xterm &'
    },
    # for debugging
    'Delete': {'modifier': X.Mod1Mask | X.Mod2Mask, 'function': 'restart'},
    'equal': {'modifier': X.Mod1Mask | X.Mod2Mask, 'function': 'exit'},
}


def restart():
    print("Restarting %s...", sys.argv[0])
    os.execvp(sys.argv[0], [sys.argv[0]])


def exit():
    print("Terminating...")
    sys.exit()


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

    def grab_keys(self):
        for string, entry in KEYBOARD_HANDLER.items():
            keysym = XK.string_to_keysym(string)
            keycode = self.dpy.keysym_to_keycode(keysym)
            if not keycode:
                continue

            modifier = entry.get('modifier', X.NONE)
            self.dpy_root.grab_key(keycode, modifier, True, X.GrabModeAsync, X.GrabModeAsync)
            self.key_handlers[keycode] = entry
            print("Grab key: %s, %s", string, entry)

    def handle_keypress(self, ev):
        keycode = ev.detail
        entry = self.key_handlers.get(keycode, None)
        if not entry:
            return

        print("Keypress: %s -> %s", keycode, entry)
        args = entry.get('args', None)
        if 'method' in entry:
            method = getattr(self, entry['method'], None)
            if method:
                if args is not None:
                    method(args)
                else:
                    method(ev)
            else:
                print("Method not reachable: %s", entry['method'])
        elif 'function' in entry:
            function = globals().get(entry['function'], None)
            if function:
                if args is not None:
                    function(args)
                else:
                    function()
            else:
                print("Function not reachable: %s", entry['function'])
        elif 'command' in entry:
            os.system(entry['command'])

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
        screen_dimensions = self.dpy_root.get_geometry()
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
        self.deskbar.fill_rectangle(self.deskbar_gc, 5, 5, 10, 10)
        self.deskbar.draw_text(self.deskbar_gc, 20, 15, self.session_info.session_name)
        self.deskbar.draw_text(self.deskbar_gc, 120, 15, self.session_info.kernel_version)
    
    def window_list(self):
        return [x for x in self.dpy_root.get_full_property(self.dpy.intern_atom('_NET_CLIENT_LIST'), Xatom.WINDOW).value]

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

    def decorate_window(self, ev):
        self.set_cursor(ev.window)
        # Move new window out of the way of the deskbar
        if AUTO_WINDOW_PLACE is True:
            if self.is_dock(ev.window) is False:
                current_x, current_y = ev.x, ev.y
                new_x = current_x + 10
                new_y = current_y + 30
                current_dimensions = self.get_window_geometry(ev.window)
                ev.window.configure(
                    x=new_x,
                    y=new_y,
                    width=current_dimensions.width,
                    height=current_dimensions.height
                )
                self.set_unfocus_window_border(ev.window)

    def raise_window(self, window):
        if not self.is_managed_window(window):
            return
        window.configure(stack_mode=X.Above)
        self.last_raised_window = window

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

    def cb_raise_or_lower_window(self, event):
        window = event.child
        self.raise_or_lower_window(window)

    def cb_focus_next_window(self, event):
        window = event.child
        self.focus_next_window(window)

    def set_unfocus_window_border(self, window):
        border_color = self.colormap.alloc_named_color(\
            "#000000").pixel
        window.configure(border_width=1)
        window.change_attributes(None, border_pixel=border_color)

    def set_focus_window_border(self, window):
        border_color = self.colormap.alloc_named_color(\
            "#ff0000").pixel
        window.configure(border_width=1)
        window.change_attributes(None, border_pixel=border_color)

    def loop(self):
        while 1:
            ev = self.dpy.next_event()

            if ev.type == X.CreateNotify:
                try:
                    self.manage_window(ev.window)
                    self.decorate_window(ev)
                except AttributeError:
                    print("Unable to handle new window")
                    pass
            elif ev.type == X.KeyPress and ev.child == X.NONE:
                self.handle_keypress(ev)
            elif ev.type == X.KeyPress and ev.child != X.NONE:
                ev.child.raise_window()
            elif ev.type == X.ButtonPress and ev.child != X.NONE:
                ev.child.raise_window()
                self.attr = ev.child.get_geometry()
                self.start = ev
            elif ev.type == X.MotionNotify and self.start:
                xdiff = ev.root_x - self.start.root_x
                ydiff = ev.root_y - self.start.root_y
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

        for child in self.dpy_root.query_tree().children:
            if child.get_attributes().map_state:
                self.manage_window(child)
            for window in self.managed_windows:
                self.set_unfocus_window_border(window)
            window = self.managed_windows[-1]
            self.focus_window(window)

        # Event loop
        try:
            self.loop()
        except KeyboardInterrupt:
            sys.exit(0)


if __name__ == "__main__":
    session_info = SessionInfo()
    session = Session(session_info=session_info)
    session.main()


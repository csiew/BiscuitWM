# requires python-xlib

from Xlib.display import Display
from Xlib import X, XK, Xatom, Xcursorfont
import sys


class DeskBar:
    def __init__(self, display, msg):
        self.display = display
        self.msg = msg
        self.start = None
        self.attr = None

        self.screen = self.display.screen()
        screen_dimensions = self.screen.root.get_geometry()
        screen_width, screen_height = screen_dimensions.width, screen_dimensions.height
        self.window = self.screen.root.create_window(
            0, 0, screen_width, 20, 1,
            self.screen.root_depth,
            background_pixel=self.screen.white_pixel,
            event_mask=X.ExposureMask | X.KeyPressMask,
        )
        self.gc = self.window.create_gc(
            foreground=self.screen.black_pixel,
            background=self.screen.white_pixel,
        )

        self.window.map()

    def loop(self):
        while True:
            e = self.display.next_event()

            if e.type == X.Expose:
                self.window.fill_rectangle(self.gc, 0, 0, 20, 20)
                self.window.draw_text(self.gc, 25, 15, self.msg)
            elif e.type == X.ButtonPress:
                self.attr = self.window.get_geometry()
                self.start = e
            elif e.type == X.MotionNotify and self.start:
                xdiff = e.root_x - self.start.root_x
                ydiff = e.root_y - self.start.root_y
                self.start.child.configure(
                    x=self.attr.x + (self.start.detail == 1 and xdiff or 0),
                    y=self.attr.y + (self.start.detail == 1 and ydiff or 0),
                    width=max(1, self.attr.width + (self.start.detail == 3 and xdiff or 0)),
                    height=max(1, self.attr.height + (self.start.detail == 3 and ydiff or 0))
                )
            elif e.type == X.ButtonRelease:
                self.start = None
                self.attr = None


class BiscuitSession:
    def __init__(self):
        self.dpy = Display()
        self.dpy_root = self.dpy.screen().root
        self.start = None
        self.attr = None
        self.set_cursor(self.dpy_root)

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
        self.dpy.flush()
    
    def window_list(self):
        return [x for x in self.dpy_root.get_full_property(self.dpy.intern_atom('_NET_CLIENT_LIST'), Xatom.WINDOW).value]

    def raise_window(self, window):
        window.configure(stack_mode=X.Above)
        self.dpy.flush()

    def event_handler(self, ev):
        if ev.type == X.CreateNotify and ev.child != X.NONE:
            print("New window created")
            self.set_cursor(ev.child)
        elif ev.type == X.KeyPress and ev.child != X.NONE:
            self.raise_window(ev.child)
        elif ev.type == X.ButtonPress and ev.child != X.NONE:
            self.raise_window(ev.child)
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
        self.dpy.flush()
    
    def main(self):
        # Register keyboard and mouse events
        self.dpy_root.grab_key(
            self.dpy.keysym_to_keycode(XK.string_to_keysym("F1")),
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

        DeskBar(self.dpy, "BiscuitWM").loop()

        # Event loop
        while True:
            ev = self.dpy.next_event()
            self.event_handler(ev)


session = BiscuitSession()
session.main()


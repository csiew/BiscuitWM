# requires python-xlib

from Xlib.display import Display
from Xlib import X, XK, Xatom, Xcursorfont
import sys
from os import system


class Session:
    def __init__(self):
        self.dpy = Display()
        self.dpy_root = self.dpy.screen().root
        self.start = None
        self.attr = None

        self.deskbar = None
        self.deskbar_gc = None

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

    def draw_deskbar(self):
        screen_dimensions = self.dpy_root.get_geometry()
        screen_width, screen_height = screen_dimensions.width, screen_dimensions.height
        self.deskbar = self.dpy_root.create_window(
            -1, -1, screen_width, 20, 1,
            self.dpy.screen().root_depth,
            background_pixel=self.dpy.screen().white_pixel,
            event_mask=X.ExposureMask | X.KeyPressMask,
        )
        self.deskbar_gc = self.deskbar.create_gc(
            foreground=self.dpy.screen().black_pixel,
            background=self.dpy.screen().white_pixel,
        )
        self.deskbar.map()
        self.draw_deskbar_content()

    def draw_deskbar_content(self):
        self.deskbar.fill_rectangle(self.deskbar_gc, 5, 5, 10, 10)
        self.deskbar.draw_text(self.deskbar_gc, 20, 15, "BiscuitWM")
    
    def window_list(self):
        return [x for x in self.dpy_root.get_full_property(self.dpy.intern_atom('_NET_CLIENT_LIST'), Xatom.WINDOW).value]

    def raise_window(self, window):
        window.configure(stack_mode=X.Above)

    def loop(self):
        while 1:
            ev = self.dpy.next_event()
            if ev.type == X.CreateNotify and ev.child != X.NONE:
                self.set_cursor(ev.child)
                # Move new window out of the way of the deskbar
                current_x, current_y = ev.root_x, ev.root_y
                current_dimensions = ev.child.get_geometry()
                ev.child.configure(
                    x=current_x+10,
                    y=current_y+20,
                    width=current_dimensions.width,
                    height=current_dimensions.height
                )
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

        # Draw deskbar
        self.draw_deskbar()

        # Event loop
        try:
            self.loop()
        except KeyboardInterrupt:
            sys.exit(0)


if __name__ == "__main__":
    Session().main()


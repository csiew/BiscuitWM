from Xlib.display import Display
from Xlib import X, XK, Xatom, Xcursorfont
import sys
from os import system


class DeskBar:
    def __init__(self):
        self.dpy = Display()
        self.dpy_root = self.dpy.screen().root
        self.deskbar = None
        self.deskbar_gc = None

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

    def loop(self):
        self.dpy_root.grab_button(
            1,
            X.NONE,
            1,
            X.ButtonPressMask,
            X.GrabModeAsync,
            X.GrabModeAsync,
            X.NONE,
            X.NONE
        )
        while 1:
            ev = self.dpy.next_event()
            if ev.type == X.Expose:
                self.draw_deskbar_content()
            elif ev.type == X.ButtonPress:
                print("Deskbar clicked")
                self.dpy_root.configure(stack_mode=X.Above)
                system("xterm")
            elif ev.type == X.Above:
                print("Deskbar raised")
            self.dpy.flush()

    def main(self):
        try:
            self.loop()
        except KeyboardInterrupt:
            sys.exit(0)


if __name__ == "__main__":
    DeskBar().main()

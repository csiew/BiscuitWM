from Xlib.display import Display
from Xlib import X, XK, Xatom, Xcursorfont


class BiscuitSession:
    def __init__(self):
        self.dpy = Display()
        self.dpy_root = self.dpy.screen().root
        self.start = None

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
        self.dpy.sync()
    
    def window_list(self):
        return [x for x in self.dpy_root.get_full_property(self.dpy.intern_atom('_NET_CLIENT_LIST'), Xatom.WINDOW).value]

    def event_handler(self, ev):
        if ev.type == X.CreateNotify and ev.child != X.NONE:
            print("New window created")
            self.set_cursor(ev.child)
        elif ev.type == X.KeyPress and ev.child != X.NONE:
            ev.child.configure(stack_mode=X.Above)
        elif ev.type == X.ButtonPress and ev.child != X.NONE:
            ev.child.configure(stack_mode=X.Above)
            attr = ev.child.get_geometry()
            self.start = ev
        elif ev.type == X.MotionNotify and self.start:
            xdiff = ev.root_x - self.start.root_x
            ydiff = ev.root_y - self.start.root_y
            self.start.child.configure(
                x = attr.x + (self.start.detail == 1 and xdiff or 0),
                y = attr.y + (self.start.detail == 1 and ydiff or 0),
                width = max(1, attr.width + (self.start.detail == 3 and xdiff or 0)),
                height = max(1, attr.height + (self.start.detail == 3 and ydiff or 0)))
        elif ev.type == X.ButtonRelease:
            self.start = None
        self.dpy.flush()
    
    def observer(self):
        # Register keyboard and mouse events
        self.dpy_root.change_attributes(event_mask=X.ButtonPressMask | X.ButtonReleaseMask | X.KeyPressMask)
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

        # Set cursor
        self.set_cursor(self.dpy_root)

        # Event loop
        while True:
            ev = self.dpy.next_event()
            self.event_handler(ev)


session = BiscuitSession()
session.observer()


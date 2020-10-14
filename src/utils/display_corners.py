"""
Thanks to vulkd for creating xround
https://github.com/vulkd/xround
"""
import sys
from Xlib import X, Xatom
from Xlib.ext import shape
from x11util import load_font
from models.pixel_palette import PixelPalette

from globals import *


class DisplayCorners(object):
    def __init__(
            self, ewmh, dpy, dpy_root, screen, display_dimensions,
            wm_window_type, wm_window_types, wm_state, wm_window_status
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

        self.bg_size = 16
        self.corners = ['nw', 'ne', 'se', 'sw']

        self.display_corners = None

        self.has_run = False

    def draw_corner_pixmap(self, window, arc_start, arc_one, arc_two, pos_in_x=0, pos_in_y=0):
        corner_pm = window.create_pixmap(self.bg_size, self.bg_size, 1)
        corner_gc = corner_pm.create_gc(foreground=1, background=1)
        corner_pm.fill_rectangle(corner_gc, 0, 0, self.bg_size, self.bg_size)
        corner_gc.change(foreground=0)
        corner_pm.fill_arc(corner_gc, pos_in_x, pos_in_y, self.bg_size, self.bg_size, arc_start, arc_one * arc_two)
        return corner_pm

    def draw_corner(self, window, arc_start, arc_one, arc_two, pos_x, pos_y, pos_in_x=0, pos_in_y=0):
        corner_pixmap = self.draw_corner_pixmap(window, arc_start, arc_one, arc_two, pos_in_x, pos_in_y)

        if not self.has_run:
            window.shape_mask(shape.SO.Set, shape.SK.Bounding, pos_x, pos_y, corner_pixmap)
            self.has_run = True
        else:
            window.shape_mask(shape.SO.Union, shape.SK.Bounding, pos_x, pos_y, corner_pixmap)
        return

    def draw(self):
        bg_pm = self.dpy_root.create_pixmap(self.bg_size, self.bg_size, self.screen.root_depth)
        bg_gc = self.dpy_root.create_gc(foreground=self.screen.black_pixel, background=self.screen.black_pixel)
        bg_pm.fill_rectangle(bg_gc, 0, 0, self.bg_size, self.bg_size)

        self.display_corners = self.dpy_root.create_window(
            0, 0, self.display_dimensions.width, self.display_dimensions.height, 0,
            self.screen.root_depth,
            background_pixmap=bg_pm,
            event_mask=X.StructureNotifyMask
        )

        sz = self.bg_size // 2
        if "nw" in self.corners:  # Check for the co-ord in corners array (that can be changed by user)
            self.draw_corner(self.display_corners, 11520, -90, 64, -sz, -sz, sz, sz)
        if "ne" in self.corners:
            self.draw_corner(self.display_corners, 0, 90, 64, self.display_dimensions.width - sz, -sz, -sz, sz)
        if "se" in self.corners:
            self.draw_corner(self.display_corners, 0, -90, 64, self.display_dimensions.width - sz,
                             self.display_dimensions.height - sz, -sz, -sz)
        if "sw" in self.corners:
            self.draw_corner(self.display_corners, -5760, -90, 64, -sz, self.display_dimensions.height - sz, sz, -sz)

        self.display_corners.shape_select_input(0)
        self.display_corners.change_property(self.wm_window_type, Xatom.ATOM, 32, [self.wm_window_types["dock"]],
                                             X.PropModeReplace)

        self.ewmh.setWmState(self.display_corners, 1, "_NET_WM_DESKTOP")
        self.ewmh.setWmState(self.display_corners, 1, "_NET_WM_STATE_SKIP_TASKBAR")
        self.ewmh.setWmState(self.display_corners, 1, "_NET_WM_STATE_ABOVE")

        self.display_corners.map()
        self.update()

    def update(self):
        self.display_corners.raise_window()

    def stop(self):
        sys.exit(0)


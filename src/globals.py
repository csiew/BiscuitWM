from Xlib import X


FONT_OPTIONS = {
    1: '-adobe-helvetica-bold-r-normal--*-120-*-*-*-*-iso8859-*',
    2: '5x7',
    3: '6x10',
    4: '7x13',
    5: '9x15',
    6: '10x20',
    7: '-misc-fixed-medium-r-normal--8-80-75-75-c-50-iso10646-1',
    8: '-misc-fixed-medium-r-semicondensed--13-120-75-75-c-60-iso10646-1',
    9: '-misc-fixed-medium-r-normal--14-130-75-75-c-70-iso10646-1',
    10: '-misc-fixed-medium-r-normal--13-120-75-75-c-80-iso10646-1',
    11: '-misc-fixed-medium-r-normal--18-120-100-100-c-90-iso10646-1',
    12: '-misc-fixed-medium-r-normal--20-200-75-75-c-100-iso10646-1',
    13: '8x13',
    14: '6x13'
}
FONT_NAME = FONT_OPTIONS[1]
CONFIG_FILE_PATH = "/etc/biscuitwm/biscuitwm.json"
recognised_events = {
    X.CreateNotify: "CreateNotify",
    X.DestroyNotify: "DestroyNotify",
    X.MapNotify: "MapNotify",
    X.FocusIn: "FocusIn",
    X.FocusOut: "FocusOut",
    X.EnterNotify: "EnterNotify",
    X.LeaveNotify: "LeaveNotify",
    X.MotionNotify: "MotionNotify",
    X.KeyPress: "KeyPress",
    X.KeyRelease: "KeyRelease",
    X.ButtonPress: "ButtonPress"
}
controller_key_names = [
    'BackSpace',
    'Control',
    'Alt',
    'Shift'
    'Tab'
]
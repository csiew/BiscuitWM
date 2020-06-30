# BiscuitWM
**BiscuitWM** is an X11 window manager based on the Python version of [TinyWM](https://github.com/mackstann/tinywm) by Nick Welch ([mackstann](https://github.com/mackstann)) with further improvements based by [nightuser](https://stackoverflow.com/users/954532/nightuser) on a Stackoverflow [thread](https://stackoverflow.com/q/7484283). The intent of this window manager project is largely to expand my understanding of the X11 libraries via Python.

Development and testing is being done in a Debian 10.4.0 virtual machine.

## Install guide
Before running BiscuitWM, you must have the `python-xlib` library installed. To do so, use the `pip` Python package manager to install it:
```
python -m pip install python-xlib
```
To install BiscuitWM on your system, run the `install.sh` as `sudo` (as we need to `chmod` the scripts to run the Python files):
```
sudo sh install.sh
```
To run the uninstall script, run the `uninstall.sh` script as `sudo` as well:
```
sudo sh uninstall.sh
```

## User guide
At the moment, BiscuitWM follows the hybrid keyboard and mouse driven interaction from TinyWM. Future iterations will seek to add titlebars to allow for mouse-first interactivity.

Note that whichever window your cursor is hovering over will be the active window. Future iterations will require the window to be raised by clicking on the window.

### Keyboard shortcuts
- `Alt + Left Click`: Move window
- `Alt + Left Click` and drag: Raise window
- `Alt + Right Click` and drag: Resize window
- `Alt + F1`: Raise currently focused window

## Emulation guide
Instead of constantly logging off, switching the Xsession, then logging in again to test, it will be easier to just run an embedded Xsession within your current session.

To do this, install the Xephyr package (`xserver-xephyr`). Then, open a terminal and run:
```bash
Xephyr -br -ac -noreset -screen 1024x780 :1 &
```
You should then see a Xephyr window popup (nothing will be visible since there is no window manager assigned). Then enter:
```bash
DISPLAY=:1
```
...to send commands to this new Xephyr window. Once you're done with testing, you may want to just reuse the same terminal for local commands. Thus, enter this command:
```bash
DISPLAY=:0
```
...to resume sending commands to your current Xsession.
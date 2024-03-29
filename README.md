# ![alt text](docs/images/logo-inline-32.png "BiscuitWM logo") BiscuitWM
![alt text](docs/images/screenshot4.png "BiscuitWM desktop")

## Links
* [Website](https://csiew.github.io/biscuitwm)
* [Repository](https://github.com/csiew/BiscuitWM)
* [Report issues](https://github.com/csiew/BiscuitWM/issues)
* [Trello board](https://trello.com/b/uFmpk6ZR/biscuitwm)

## Overview

**BiscuitWM** is an X11 window manager based on the Python version of [TinyWM](https://github.com/mackstann/tinywm) by [Nick Welch](https://github.com/mackstann) and the [xpywm](https://github.com/h-ohsaki/xpywm) window manager by [Hiroyuki Ohsaki](http://www.lsnl.jp/~ohsaki/). The intent of this window manager project is largely to expand my understanding of the X11 libraries via Python.

Development and testing is being done in a Debian 11 virtual machine with Python 3.9 as the main Python interpreter.

**WARNING:** This project is still in alpha. It is not recommended to run BiscuitWM on a production machine without using Xephyr to run an embedded X session!

## Install guide
Before running BiscuitWM, you must have the `python-xlib`, `x11util`, `perlcompat`, and `ewmh` libraries installed. To do so, use the `pip` Python package manager to install it:
```bash
cd /path/to/project

sudo apt update
sudo apt install python3 python3-pip

pip3 install -r requirements.txt
```
To install BiscuitWM on your system, run the `setup.sh` as `sudo` (as we need to `chmod` the scripts to run the Python files):
```bash
sudo sh scripts/setup.sh
```
To run the uninstall script, run the `purge.sh` script as `sudo` as well:
```bash
sudo sh scripts/purge.sh
```

## User guide

At the moment, BiscuitWM follows the hybrid keyboard and mouse driven interaction from TinyWM. Future iterations will seek to add titlebars to allow for mouse-first interactivity.

Note that whichever window your cursor is hovering over will be the window with input focus (and will also be raised). Future iterations will require the window to be raised by clicking on the window.

### Keyboard shortcuts
> **WARNING:** As of 17 September 2021, keyboard shortcuts are reportedly unresponsive. A solution for this issue is currently being worked on. [See issue ticket.](https://github.com/csiew/BiscuitWM/issues/4)

#### Moving windows
- `Alt + Left Click` and drag: Move window
- `Alt + Right Click` and drag: Resize window
- `Alt + Q`: Close the currently-focused window
#### Resizing windows
- `Alt + -`: Move window to center of display
- `Alt + =`: Maximize currently-focused window
- `Alt + [`: Fill left-side of the screen with currently-focused window
- `Alt + ]`: Fill right-side of the screen with currently-focused window
- `Alt + \`: Fill top of the screen with currently-focused window
- `Alt + /`: Fill bottom of the screen with currently-focused window
#### Multitasking
- `Alt + Tab`: Cycle through all windows
- `Alt + Left Click` on deskbar: Cycle through all windows
- `Alt + Right Click` on deskbar: Show number of windows
#### Launcher
- `Alt + Space`: Enables launcher mode in the top bar
- `Return`: Enter command and exit top bar launcher
- `Esc`: Exit launcher mode
#### Session
- `Alt + X`: Launch a new terminal window
- `Alt + Esc`: Exit BiscuitWM session

### Configuration
BiscuitWM can read a JSON file (stored at `/etc/biscuitwm/biscuitwm.json`) for options such as debug output, window placement, window decorations, etc.

## Emulation guide
Instead of constantly logging off, switching the Xsession, then logging in again to test, it will be easier to just run an embedded Xsession within your current session. To do this, install the Xephyr package (`xserver-xephyr`).

### Manual
Open a terminal and run:
```bash
Xephyr -br -ac -noreset -screen 1024x780 :1 &
```
You should then see a Xephyr window popup (nothing will be visible since there is no window manager assigned). Then enter:
```bash
DISPLAY=:1
```
...to send commands to this new Xephyr window.
Then start the BiscuitWM session:
```bash
biscuitwm-session
```

Once you're done with testing, you may want to just reuse the same terminal for local commands. Thus, enter this command:
```bash
DISPLAY=:0
```
...to resume sending commands to your current Xsession.

## Acknowledgements
See the [acknowledgements section of the website](https://csiew.github.io/BiscuitWM#acknowledgements) for more details.
- BiscuitWM is based off the work of Nick Welch (2005, 2011) and Hiroyuki Ohsaki (2019-Present). It also uses a code snippet by Rodrigo Silva (2016) and integrates a project by vulkd (2017, 2019).
- The project's logo uses a modified version of [this image](https://www.wallpaperflare.com/biscuit-placed-on-brown-wooden-surface-crumb-butter-biscuit-wallpaper-wcwij).

# ![alt text](docs/images/logo-inline-32.png "BiscuitWM logo") BiscuitWM
![alt text](docs/images/screenshot3.png "BiscuitWM desktop")

**BiscuitWM** is an X11 window manager based on the Python version of [TinyWM](https://github.com/mackstann/tinywm) by [Nick Welch](https://github.com/mackstann) and the [xpywm](https://github.com/h-ohsaki/xpywm) window manager by [Hiroyuki Ohsaki](http://www.lsnl.jp/~ohsaki/). The intent of this window manager project is largely to expand my understanding of the X11 libraries via Python.

Development and testing is being done in a Debian 10.4.0 virtual machine.

**WARNING:** This project is still in alpha. It is not recommended to run BiscuitWM on a production machine without using Xephyr to run an embedded X session!

## Install guide
Before running BiscuitWM, you must have the `python3-xlib`, `x11util`, and `perlcompat` libraries installed. To do so, use the `pip` Python package manager to install it:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-xlib

python3 -m pip install python-xlib x11util perlcompat
```
To install BiscuitWM on your system, run the `install.sh` as `sudo` (as we need to `chmod` the scripts to run the Python files):
```bash
sudo sh install.sh
```
To run the uninstall script, run the `uninstall.sh` script as `sudo` as well:
```bash
sudo sh uninstall.sh
```

## User guide
At the moment, BiscuitWM follows the hybrid keyboard and mouse driven interaction from TinyWM. Future iterations will seek to add titlebars to allow for mouse-first interactivity.

Note that whichever window your cursor is hovering over will be the window with input focus (and will also be raised). Future iterations will require the window to be raised by clicking on the window.

### Keyboard shortcuts
- `Alt + Left Click` and drag: Move window
- `Alt + Right Click` and drag: Resize window
- `Alt + M`: Maximize currently-focused window
- `Alt + [`: Fill left-side of the screen with currently-focused window
- `Alt + ]`: Fill right-side of the screen with currently-focused window
- `Alt + \`: Fill top of the screen with currently-focused window
- `Alt + /`: Fill bottom of the screen with currently-focused window
- `Alt + Q`: Close the currently-focused window
- `Alt + Tab`: Cycle through all windows
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

### Partially automated*
Open a terminal in the same directory as the BiscuitWM files and run:
```bash
sudo sh run_dev.sh
```
Then start the BiscuitWM session:
```bash
biscuitwm-session
```
The `run_dev.sh` script will be improved in the future.

## Acknowledgements
See the [acknowledgements section of the website](https://csiew.github.io/BiscuitWM#acknowledgements) for more details.
- BiscuitWM is based off the work of Nick Welch (2005, 2011) and Hiroyuki Ohsaki (2019-Present). It also uses a code snippet by Rodrigo Silva (2016) and integrates a project by vulkd (2017, 2019).
- The project's logo uses a modified version of [this image](https://www.wallpaperflare.com/biscuit-placed-on-brown-wooden-surface-crumb-butter-biscuit-wallpaper-wcwij).

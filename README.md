# BiscuitWM
**BiscuitWM** is an X11 window manager based on the Python version of [TinyWM](https://github.com/mackstann/tinywm) by Nick Welch ([mackstann](https://github.com/mackstann)). This window manager is largely to expand my understanding of the X11 libraries via Python.

Development and testing is being done in a Debian 10.4.0 virtual machine.

## How to emulate
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
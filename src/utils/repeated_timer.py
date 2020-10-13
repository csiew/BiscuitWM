"""
Thanks to MestreLion for their RepeatedTimer implementation
https://stackoverflow.com/a/13151299
- Standard library only, no external dependencies
- start() and stop() are safe to call multiple times even if the timer has already started/stopped
- function to be called can have positional and named arguments
- You can change interval anytime, it will be effective after next run. Same for args, kwargs and even function!
"""
from threading import Timer


class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

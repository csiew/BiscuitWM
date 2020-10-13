from utils.repeated_timer import RepeatedTimer


class DeskbarItem(object):
    def __init__(self, name, text="", width=0, interval=None, function=None, enabled=True):
        self.name = name
        self.text = text
        self.width = width
        self.interval = interval
        self.function = function
        self.enabled = enabled
        if interval is not None and function is not None:
            self.rt_event = RepeatedTimer(interval, function)
        else:
            self.rt_event = None

    def set_rt_event(self, interval, function):
        self.interval = interval
        self.function = function
        self.rt_event = RepeatedTimer(interval, function)

    def unset_rt_event(self):
        if self.rt_event is not None:
            self.rt_event.stop()
            self.rt_event = None
            self.interval = None
            self.function = None

    def start(self):
        if self.rt_event is not None:
            self.rt_event.start()

    def stop(self):
        if self.rt_event is not None:
            self.rt_event.stop()

import config
import os
import select
import struct
import threading


TIMEOUT = config.BUTTONS_POLL_TIMEOUT


class ButtonReader(threading.Thread):

    def __init__(self, filename):
        super(ButtonReader, self).__init__()
        self.daemon = True
        self.file = os.open(filename, os.O_RDONLY)
        self.struct = struct.Struct('LLHHi')
        self.callbacks = []
        self.exit_event = threading.Event()
        self.clear()

    def clear(self):
        self.keycode = None
        self.keypressed = False
        self.clicks = 0
        self.hold_cycles = 0

    def register(self, callback):
        self.callbacks.append(callback)

    def dispatch(self):
        for callback in self.callbacks:
                callback(self.keycode, self.clicks, self.hold_cycles)

    def timeout(self):
        if self.keypressed: # A key was pressed and is being held
            self.hold_cycles += 1
            self.dispatch()
        elif self.keycode: # A key was pressed and released, then a timeout occurred
            if not self.hold_cycles: # If a key was being held then dispatch would have been done already
                self.dispatch()
            self.clear()

    def press(self, keycode):
        if self.keycode and self.keycode != keycode:
            self.dispatch()
            self.clear()
        self.keycode = keycode
        self.keypressed = True

    def release(self, keycode):
        if not self.hold_cycles:
            self.clicks += 1
        self.keypressed = False

    def process_event(self, packed_event):
        sec, usec, evtype, code, value = self.struct.unpack_from(packed_event)
        if evtype == 1: # The only meaningful type for key events
            if value == 0: # Key release
                self.release(code)
            elif value == 1: # Key press
                self.press(code)

    def run(self):
        poll = select.epoll()
        poll.register(self.file, select.EPOLLIN)
        while not self.exit_event.is_set():
            events = poll.poll(TIMEOUT)
            if not events:
                self.timeout()
            for _ in events:
                packed_event = os.read(self.file, self.struct.size)
                self.process_event(packed_event)
        os.close(self.file)

    def exit(self):
        self.exit_event.set()

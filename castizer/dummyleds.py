import Queue
import threading
import time
import os


class LED(threading.Thread):

    def __init__(self, device):
        super(LED, self).__init__()
        print "dummyLED: init\n"

    def exit(self):
        print "dummyLED: exit\n"
    
    def run(self):
        print "dummyLED: run\n"
    
    def on(self):
        print "dummyLED: on\n"
    
    def off(self):
        print "dummyLED: off\n"
    
    def flip(self):
        print "dummyLED: flip\n"
    
    def fade(self, ms):
        print "dummyLED: fade\n"
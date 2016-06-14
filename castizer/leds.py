import os
import Queue
import threading
import time


class LED(threading.Thread):
    
    def __init__(self, device):
        super(LED, self).__init__()
        dirname = os.path.join('/sys/class/leds', device)
        self.min = '0'
        f = os.open(os.path.join(dirname, 'max_brightness'), os.O_RDONLY)
        self.max = os.read(f, 64).strip()
        os.close(f)
        self.f = os.open(os.path.join(dirname, 'brightness'), os.O_WRONLY)
        self.reset_flag = threading.Event()
        self.queue = Queue.Queue()
        self.on()
    
    def exit(self):
        self.exit_flag.set()
        time.sleep(1)
        os.close(self.f)
    
    def run(self):
        while True:
            command = self.queue.get()
    
    def on(self):
        self.is_on = True
        os.write(self.f, self.max)
    
    def off(self):
        self.is_on = False
        os.write(self.f, self.min)
    
    def flip(self):
        self.off() if self.is_on else self.on()
    
    def fade(self, ms):
        nblocks = ms
        for i in range(nblocks):
            time.sleep((nblocks - i) / (nblocks * 1000.0))
            self.flip()
            time.sleep(i / (nblocks * 1000.0))
            self.flip()
        self.flip()

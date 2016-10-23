#!/usr/bin/python

#In Python 3.x the strings are Unicode by default. When sending data to Arduino, they have to be converted to bytes. This can be done by prefixing the string with b:
#>>> ser.write(b'5') # prefix b is required for Python 3.x
 
import serial
import time
import sys
import config
import os
import select
import struct
import threading

baudrate = 9600

class SensorReader(threading.Thread):

    def __init__(self, filename):
        super(SensorReader, self).__init__()
        self.daemon = True
        self.struct = struct.Struct('LLHHi')
        self.callbacks = []
        self.exit_event = threading.Event()
        self.clear()
        # open serial port
        try:
            self.ser = serial.Serial(config.SENSORS_SERIAL_PORT, baudrate,timeout=None)
            print 'Serial port succesfully opened ! ', config.SENSORS_SERIAL_PORT 
        except:
            print 'Error opening serial port: <', config.SENSORS_SERIAL_PORT, '>'
            exit
        #TODO > Wait until signal from Arduino saying it is ready
	time.sleep(15)
	self.ser.write(bytearray('X','ascii'))
        #var = raw_input("Enter something: ")
        #self.ser.write(var)

    def clear(self):
        self.action = None
        self.value = None

    def register(self, callback):
        self.callbacks.append(callback)

    def dispatch(self):
        for callback in self.callbacks:
            callback(self.action, self.value)

    def run(self):
        while not self.exit_event.is_set():
            try:
                line = self.ser.readline()
                #line = ser.readline(3).decode('utf-8')[:-2]
                if line != "":
                    
                    print "LINE: <", line, ">"
                    if (line[0]=='S'):
                        if (line[1:3]=='SS'):
                            self.action = config.ACTION_JUST_BOOTED
                        elif (line[1:3]=='01'):
                            self.action = config.ACTION_SWITCH_ON
                        elif (line[1:3]=='00'):
                            self.action = config.ACTION_SWITCH_OFF
                        else:
                            self.action = config.ACTION_ERROR
                    elif (line[0]=='J'):
                        self.action = config.ACTION_JOY_BUTTON
                    elif (line[0]=='V'):
                        self.action = config.ACTION_VOLUME
                    elif (line[0]=='C'):
                        self.action = config.ACTION_CHANNEL
                    else:
                        self.action = config.ACTION_ERROR

                    if ( (line[0]=='V') or (line[0]=='C') or (line[0]=='J')): 
                        try:
                            self.value = int(line[1:3])
                            #print "SENSORS value: ", int(line[1:3])
                        except ValueError:
                            self.value = config.ACTION_ERROR
    
                    print "DEBUG: char1", line[0], "char2", line[1], "char3", line[2] 
                    print "SENSORS action: ", self.action
                    print "SENSORS value: ", self.value

                    #line = "<" + line + ">"
                    #print "SENSORS: ", line
                    #self.ser.write(line)
                    #self.ser.write('\r\n')
                    #self.ser.flush();
                    
# 
# 
# ACTION_SWITCH_ON = 0
# ACTION_SWITCH_OFF = 1
# ACTION_VOLUME = 2
# ACTION_CHANNEL = 3
# ACTION_JOY_X = 4
# ACTION_JOY_Y = 5
# ACTION_JOY_BUTTON = 6
# 
#                     
#                     
#                     
#                     
                    self.dispatch()
                    
                time.sleep(0.1)
                #ser.write(input + '\r\n')
                #packed_event = os.read(self.file, self.struct.size)
                #self.process_event(packed_event)
            except serial.SerialException as e:
                #There is no new data from serial port
                print('Data could not be read')
                time.sleep(1)
        self.ser.close()

    def exit(self):
        self.exit_event.set()

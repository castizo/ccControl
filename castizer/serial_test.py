#!/usr/bin/python

#In Python 3.x the strings are Unicode by default. When sending data to Arduino, they have to be converted to bytes. This can be done by prefixing the string with b:
#>>> ser.write(b'5') # prefix b is required for Python 3.x
 
import serial
import time
import sys
 
#port = '/dev/usb/tts/0'
port = '/dev/pts/2'
baudrate = 9600
 
# open serial port
try:
    ser = serial.Serial(port, baudrate,timeout=0.1)
except:
    print 'Error opening serial port!'
    
#TODO > Wait until signal from Arduino saying it is ready

var = raw_input("Enter something: ")
ser.write(var)

while 1:
    try:
        line = ser.readline(3)
        #line = ser.readline(3).decode('utf-8')[:-2]
        print "read!"
        if line != "":
            line = "<" + line + ">"
            print line
            ser.write(line)
            ser.write('\r\n')
            #self.ser.flush();
        time.sleep(0.1)
        #ser.write(input + '\r\n')
    except ser.SerialTimeoutException:
        print('Data could not be read')

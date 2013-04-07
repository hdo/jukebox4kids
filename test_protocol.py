#!/usr/bin/env python

import sys
import serial
import time

def main(argv):
   print "connect to serial ..."
   ser = serial.Serial('/dev/pts/3', 115200, timeout=0)
   print("connected")
   data = []
   parse_data = False
   while(1):
      selection = raw_input("select command: ")
      print selection
      if selection == '1':
         ser.write('/201\r\n')         
      if selection == '2':
         ser.write('/211\r\n')         
      if selection == '3':
         ser.write('/221\r\n')         
      if selection == '4':
         ser.write('/231\r\n')         
      if selection == 'a':
         ser.write('/11363090148171\r\n')         
      if selection == 'b':
         ser.write('/11363096305162\r\n')         
      if selection == 'c':
         ser.write('/11363096308853\r\n')         
      if selection == 'd':
         ser.write('/11363096328594\r\n')         
      if selection == 'e':
         ser.write('/11363096867555\r\n')         
      if selection == 'f':
         ser.write('/11363096867534\r\n')         
         
      # sleep for 10ms
      time.sleep(0.01)
      #print "-"
   ser.close()
   
   
if __name__ == "__main__":
   main(sys.argv[1:])
    
    


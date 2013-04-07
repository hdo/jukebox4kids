#!/usr/bin/env python

import sys
import os
import serial
import time
import string
import subprocess
import re

playlist_dir = "/var/lib/mpd/playlists"
track_count = 0
current_track = 1

def gettrack_count():
   process = subprocess.Popen(['mpc playlist | wc -l'], shell=True, stdout=subprocess.PIPE)
   (st, er) = process.communicate()
   tcount = 0
   try:
      tcount = int(st.strip())
   except ValueError, ex:
      print '"%s" cannot be converted to an int: %s' % (value, ex)
   return tcount

def getPlayStatus():
   process = subprocess.Popen(['mpc'], shell=True, stdout=subprocess.PIPE)
   (st, er) = process.communicate()
   track_count = 0
   current_track = 0
   play_status = 0
   
   try:
      found = re.findall('\[(.*?)\]', st)
      if len(found) > 0:
         if found[0] == 'paused':
            play_status = 1
         else:
            play_status = 2
      found = re.findall('#(.*?)/', st)
      if len(found) > 0:
         current_track = int(found[0].strip())
      found = re.findall('#.*/(.*?)\s\s', st)
      if len(found) > 0:
         track_count = int(found[0].strip())
   except ValueError, ex:
      print '"%s" cannot be converted to an int: %s' % (value, ex)
   return (current_track, track_count, play_status)



def loadPlaylist(pls):
   global current_track
   global track_count
   pls_file = os.path.join(playlist_dir, "%s.m3u" % pls)
   print pls_file
   if os.path.exists(pls_file):
      print "loading playlist: %s" % pls
      os.system("mpc stop")
      os.system("mpc clear")
      os.system("mpc load %s" % pls)
      track_count = gettrack_count()
      current_track = 1
      if track_count > 0:
         os.system("mpc play 1")
   else:
      print "playlist not found!"

def sendButton(button, ser):
   global current_track
   global track_count
   temp = current_track
   if track_count == 0:
      track_count = gettrack_count()
      if track_count > 0:
         current_track = 1 
   if button == '1':
      if current_track > 1:
         current_track = current_track - 1
         os.system("mpc play %d " % current_track)
   if button == '2':
      os.system("mpc toggle")
   if button == '3':
      if current_track < track_count:
         current_track = current_track + 1
         os.system("mpc play %d " % current_track)

def update_display_old(ser):
   global current_track
   d1 = str(current_track / 10)[0]
   d0 = str(current_track % 10)[0]
   cmd = '/L:%s%s\n' % (d1, d0)
   ser.write(cmd)
   ser.flush()

def update_display(ser):
   global current_track
   global track_count
   (current_track, track_count, play_status) = getPlayStatus()      
   d1 = str(current_track / 10)[0]
   d0 = str(current_track % 10)[0]
   cmd = '/L:%s%s\n' % (d1, d0)
   ser.write(cmd)
   ser.flush()
   if play_status == 1:
      cmd = '/D:19n'
   else:
      cmd = '/D:0\n'
   ser.write(cmd)
   ser.flush()
     

def main(argv):
   global current_track, track_count
   print "connect to serial ..."
   #ser = serial.Serial('/dev/pts/4', 115200, timeout=0)
   ser = serial.Serial('/dev/ttyAMA0', 115200, timeout=0)
   print("connected")
   # send heart beat
   ser.write('/H:foo\r\n')
   ser.write('/H:foo\r\n')
   # send i'm online
   ser.write('/O:foo\n')
   ser.flush()
   data = []
   parse_data = False
   current_barcode = ""
   update_display(ser)
   last_ms = time.time()
   while(1):
      try:
         buf = ser.read(100)
         if len(buf) > 0:
            for d in buf:
               #print ord(d)
               if ord(d) == 13 or ord(d) == 10:
                  parse_data = True
               else:   
                  data.append(d)               
         if parse_data:
            parse_data = False
            print data
            if not data[0] == '/':
               # error
               print "protocol error, message: %s" % data
            if data[1] == 'B' and len(data) > 10:
               # barcode id
               barcode = string.join(data[3:-1], "")
               print "receiving barcode: %s" % barcode
               if not barcode == current_barcode:
                  current_barcode = barcode
                  loadPlaylist(barcode)
            if data[1] == 'S' and len(data) > 3:
               button_index = data[3]
               print "button %s pressed" % button_index
               sendButton(button_index, ser)
            #print data
            data = []
            update_display(ser)

            
         # sleep for 10ms
         time.sleep(0.01)
         current_ms = time.time()
         
         if (current_ms - last_ms) > 0.5:
            last_ms = current_ms
            update_display(ser)
      except Exception as ex:
         print 'Error: an error occurred during execution: %s' % (ex)
         current_barcode = ""
         current_track = 0
         track_count = 0
   ser.close()
   
   
if __name__ == "__main__":
   main(sys.argv[1:])
    
    

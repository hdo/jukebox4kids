#!/usr/bin/env python
import os, sys, getopt
import time
from os.path import expanduser


#music_dir = "/data/temp/mpd_test"
music_dir = "/data/hdo/kinder"
#music_dir = "/mediafiles"
playlist_dir = "/var/lib/mpd/playlists"
#playlist_dir = "/data/temp/mpd_test/_jukeboxpls"
rfid_map_file = "rfidmap.properties"
#temp_dir = "/data/temp/mpd_test"
#temp_dir = "/home/pi/temp"
temp_dir = "/home/huy/pi/temp"


def hasMediaFiles(path):
   for filename in sorted(os.listdir(path)):
      if filename.endswith('.mp3'):
         return True
   return False


def new_id():
    time.sleep(0.02)
    ret = str(time.time()).replace('.','')
    if len(ret) < 12:
      ret = ret + '0'    
    return ret


def getFolderListRecursive(path):
   flist = []
   flist.append(path)
   retlist = []
   while len(flist) > 0:
      current_f = flist.pop(0)
      for element in os.listdir(current_f):
         if os.path.isdir(element):
            new_path = os.path.join(current_f, element)
            flist.append()

      
def save_playlist(playlist, barcodeid):
   if len(playlist) > 0 and len(barcodeid) > 0:
      print "saving playlist with %d entries" % len(playlist)     
      fname = os.path.join(playlist_dir, "%s.m3u" % barcodeid)
      output = open(fname,'w')
      for item in playlist:
         output.write(item)
         output.write("\n")
      output.close()
   

def getRFIDs(rfidfile):
    rfidlist = []
    if os.path.exists(rfidfile) and os.path.isfile(rfidfile):
        for line in open(rfidfile):
            rfid = line.strip()
            if rfid and len(rfid) > 0:
                rfidlist.append(rfid)
    return rfidlist


def createRFIDMap(rfid_work_map):
    rfid_map = []
    for (barcodeid, rfidfile) in rfid_work_map:
        rfidlist = getRFIDs(rfidfile)
        for rfid in rfidlist:
            rfid_map.append((rfid, barcodeid))
    return rfid_map


def saveRFIDMap(rfid_map):
    print "saving %s with %d entries" % (rfid_map_file, len(rfid_map))
    f = open(rfid_map_file, 'w')
    for (rfid, barcode) in rfid_map:
        entry = "%s=%s\n" % (rfid, barcode)
        f.write(entry)
    f.close()

def load_rfid_map(rfid_map_file):
    print "loading %s" % rfid_map_file
    rfid_map = []
    for line in open(rfid_map_file, 'r'):
        data = line.strip()
        if len(data) > 0:
            index = data.find('=')
            if index > 0:
                rfid = data[0:index]
                barcode = data[index+1:]
                rfid_map.append((rfid, barcode))
    return rfid_map

def main(argv):
    allsongs_file = os.path.join(temp_dir, 'all.txt')
    cmd = 'mpc listall > "%s"' % allsongs_file
    print cmd
    os.system(cmd)

    current_playlist = []
    current_id = ""
    last_dirname = ""
    rfidfile = ""
    rfid_work_map = []

    f = open(allsongs_file)
    for line in f:
        line = line.strip()      
        dname = os.path.dirname(line)
        if not dname == last_dirname:                         
            save_playlist(current_playlist, current_id)
            rfid_work_map.append((current_id, rfidfile))
            current_playlist = []
         
            print "preparing new playlist"
            path = os.path.join(music_dir, dname)
            idfile = os.path.join(path, 'barcode.id')
            rfidfile = os.path.join(path, 'rfid.id')
            print idfile
            if not os.path.exists(idfile):
                print "ERROR: missing bardcode.id file in %s" % path
                continue
            else:
                current_id = str(open(idfile).read()).strip()
        else:
            print os.path.dirname(line)
         
        current_playlist.append(line)
        last_dirname = dname
    # save last open playlist
    save_playlist(current_playlist, current_id)
    rfid_work_map.append((current_id, rfidfile))

    print "preparing rfid mapping ..."
    rfid_map = createRFIDMap(rfid_work_map)
    saveRFIDMap(rfid_map)
    for item in load_rfid_map(rfid_map_file):
        print item
    print "done."
   
if __name__ == "__main__":
    main(sys.argv[1:])

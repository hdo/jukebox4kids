#!/usr/bin/env python
import os, sys, getopt
import time
from os.path import expanduser


music_dir = "/data/temp/kinder/music"
playlist_dir = "/data/temp/kinder/playlists"
rfid_map_file = "/home/pi/pyjukebox/rfidmap.properties"
temp_dir = "/data/temp/kinder"


def save_playlist(playlist, barcodeid):
   if len(playlist) > 0 and len(barcodeid) > 0:
      print "saving playlist with %d entries" % len(playlist)     
      fname = os.path.join(playlist_dir, "%s.m3u" % barcodeid)
      output = open(fname,'w')
      for item in playlist:
         output.write(item)
         output.write("\n")
      output.close()
   
def main(argv):
    allsongs_file = os.path.join(temp_dir, 'all.txt')
    cmd = 'mpc listall > "%s"' % allsongs_file
    print cmd
    os.system(cmd)

    current_playlist = []
    current_id = ""
    last_dirname = ""

    f = open(allsongs_file)
    for line in f:
        line = line.strip()      
        dname = os.path.dirname(line)
        if not dname == last_dirname:                         
            save_playlist(current_playlist, current_id)
            current_playlist = []
         
            print "preparing new playlist"
            path = os.path.join(music_dir, dname)
            idfile = os.path.join(path, 'rfid.id')
            print idfile
            if not os.path.exists(idfile):
                print "ERROR: missing rfid.id file in %s" % path
                continue
            else:
                current_id = str(open(idfile).read()).strip()
        else:
            print os.path.dirname(line)
         
        current_playlist.append(line)
        last_dirname = dname
    # save last open playlist
    save_playlist(current_playlist, current_id)
   
if __name__ == "__main__":
    main(sys.argv[1:])

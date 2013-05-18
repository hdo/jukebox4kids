#!/usr/bin/env python

import sys
import os
import serial
import time
import string
import subprocess
import re


class Jukebox4Kids:

    def __init__(self):
        self.playlist_dir = "/var/lib/mpd/playlists"
        self.rfid_map_file = "rfidmap.properties"
        self.track_count = 0
        self.current_track = 1
        self.play_status = 0
        self.is_sleep_mode = False
        self.last_activity_check_ms = 0.0
        self.last_activity_ms = 0.0
        self.sleep_mode_ms = 0.0
        self.go_sleep_mode_time_out = 600
        self.go_standby_mode_time_out = 7200
        #self.power_off_amp_time_out = 120
        self.power_off_amp_time_out = 30
        self.rfid_map = []


    def load_rfid_map(self):
        print "loading %s" % self.rfid_map_file
        if not os.path.exists(self.rfid_map_file):
            print "could not open %s" % self.rfid_map_file
            return
        self.rfid_map = []
        for line in open(self.rfid_map_file, 'r'):
            data = line.strip()
            if len(data) > 0:
                index = data.find('=')
                if index > 0:
                    rfid = data[0:index]
                    barcode = data[index+1:]
                    self.rfid_map.append((rfid, barcode))

    def get_barcode_by_rfid(rfid):
        for (rf, bc) in self.rfid_map:
            if rfid == rf:
                return bc
        return

    def get_track_count(self):
        process = subprocess.Popen(['mpc playlist | wc -l'], shell=True, stdout=subprocess.PIPE)
        (st, er) = process.communicate()
        tcount = 0
        try:
            tcount = int(st.strip())
        except ValueError, ex:
            print '"%s" cannot be converted to an int: %s' % (st, ex)
        return tcount

    def get_play_status(self):
        process = subprocess.Popen(['mpc'], shell=True, stdout=subprocess.PIPE)
        (st, er) = process.communicate()
        self.track_count = 0
        self.current_track = 0
        self.play_status = 0

        try:
            found = re.findall('\[(.*?)\]', st)
            if len(found) > 0:
                if found[0] == 'paused':
                    self.play_status = 1
                else:
                    # playing
                    self.play_status = 2
            found = re.findall('#(.*?)/', st)
            if len(found) > 0:
                self.current_track = int(found[0].strip())
            found = re.findall('#.*/(.*?)\s\s', st)
            if len(found) > 0:
                self.track_count = int(found[0].strip())
        except ValueError, ex:
            print '"%s" cannot be converted to an int: %s' % (found[0], ex)

    def load_playlist(self, pls):
        if self.is_sleep_mode:
            return

        pls_file = os.path.join(self.playlist_dir, "%s.m3u" % pls)
        #print pls_file
        if os.path.exists(pls_file):
            print "loading playlist: %s" % pls
            os.system("mpc stop")
            os.system("mpc clear")
            os.system("mpc load %s" % pls)
            self.track_count = self.get_track_count()
            self.current_track = 1
            if self.track_count > 0:
                os.system("mpc play 1")
        else:
            print "playlist not found!"

    def go_sleep(self):
        if self.is_sleep_mode:
            return
        os.system("mpc pause")
        cmd = '/l:R1\n'
        self.ser.write(cmd)
        self.ser.flush()
        cmd = '/l:G1\n'
        self.ser.write(cmd)
        self.ser.flush()
        cmd = '/D:0\n'
        self.ser.write(cmd)
        self.ser.flush()
        self.is_sleep_mode = True
        self.sleep_mode_ms = time.time()

    def go_wakeup(self):
        # transition from sleep to online
        cmd = '/l:R0\n'
        self.ser.write(cmd)
        self.ser.flush()
        cmd = '/l:G1\n'
        self.ser.write(cmd)
        self.ser.flush()
        cmd = '/D:1\n'
        self.ser.write(cmd)
        self.ser.flush()
        self.is_sleep_mode = False
        cmd = '/P:A1\n'
        self.ser.write(cmd)
        self.ser.flush()


    def go_power_off_amp(self):
        cmd = '/P:A0\n'
        self.ser.write(cmd)
        self.ser.flush()

    def go_stand_by(self):
        cmd = '/S:30\n'
        self.ser.write(cmd)
        self.ser.flush()

    def process_button(self, button):
        if self.track_count == 0:
            self.track_count = self.get_track_count()
            if self.track_count > 0:
                self.current_track = 1

        # ON/OFF
        if button == '0':
            print "on/off"
            if not self.is_sleep_mode:
                self.go_sleep()
            else:
                self.go_wakeup()

        # ignore other buttons if in sleep mode
        if self.is_sleep_mode:
            return

        # PREV
        if button == '1':
            if self.current_track > 1:
                self.current_track = self.current_track - 1
                os.system("mpc play %d " % self.current_track)

        # PLAY/PAUSE
        if button == '2':
            os.system("mpc toggle")

        # NEXT
        if button == '3':
            if self.current_track < self.track_count:
                self.current_track = self.current_track + 1
                os.system("mpc play %d " % self.current_track)

    def update_display(self):
        if self.is_sleep_mode:
            return
        d1 = str(self.current_track / 10)[0]
        d0 = str(self.current_track % 10)[0]
        cmd = '/L:%s%s\n' % (d1, d0)
        self.ser.write(cmd)
        self.ser.flush()
        if self.play_status == 1:
            # enabled blink
            cmd = '/D:3\n'
        else:
            # disable blink
            cmd = '/D:2\n'
        self.ser.write(cmd)
        self.ser.flush()

    def check_activity(self):
        current_ms = time.time()
        if self.play_status == 2:
            self.last_activity_ms = current_ms
            return
        if current_ms - self.last_activity_ms > self.go_sleep_mode_time_out:
            # enter sleep
            print "entering sleep mode"
            self.go_sleep()
        if current_ms - self.last_activity_ms > self.go_standby_mode_time_out:
            # enter stand-by
            print "entering stand-by mode"
        if self.is_sleep_mode and current_ms - self.sleep_mode_ms > self.power_off_amp_time_out:
            # power off amp
            print "powering off amp"
            self.go_power_off_amp()

    def run(self):
        self.load_rfid_map()
        print "connect to serial ..."
        #ser = serial.Serial('/dev/pts/4', 115200, timeout=0)
        self.ser = serial.Serial('/dev/ttyAMA0', 115200, timeout=0)
        print("connected")
        # send heart beat
        self.ser.write('/H:foo\r\n')
        self.ser.write('/H:foo\r\n')
        # send i'm online
        self.ser.write('/O:foo\n')
        self.ser.flush()
        data = []
        parse_data = False
        current_barcode = ""
        self.update_display()
        last_ms = time.time()
        while(1):
            try:
                buf = self.ser.read(100)
                if len(buf) > 0:
                    for d in buf:
                        #print ord(d)
                        if ord(d) == 13 or ord(d) == 10:
                            parse_data = True
                        else:
                            data.append(d)
                if parse_data:
                    parse_data = False
                    #print data
                    if not data[0] == '/':
                        # error
                        print "protocol error, message: %s" % data
                    if data[1] == 'B' and len(data) > 10:
                        # barcode id
                        barcode = string.join(data[3:-1], "")
                        print "receiving barcode: %s" % barcode
                        if not barcode == current_barcode:
                            current_barcode = barcode
                            self.load_playlist(barcode)
                    if data[1] == 'R' and len(data) > 6:
                        # barcode id
                        rfid = string.join(data[3:], "")
                        print "receiving rfid: %s" % rfid
                        barcode = rfid
                        if  rfid == '6911395':
                            barcode = '136309014817'
                        elif rfid == '687220':
                            barcode = 'radio'
                        else:
                            barcode = get_barcode_by_rfid(rfid)
                        if not barcode == current_barcode:
                            current_barcode = barcode
                            self.load_playlist(barcode)
                    if data[1] == 'S' and len(data) > 3:
                        button_index = data[3]
                        print "button %s pressed" % button_index
                        self.process_button(button_index)
                    #print data
                    data = []
                    self.update_display()
                    last_ms = time.time()
                    self.last_activity_check_ms = last_ms
                    self.last_activity_ms = last_ms

                # sleep for 10ms
                time.sleep(0.01)
                current_ms = time.time()

                # update display each 0.5 seconds
                if (current_ms - last_ms) > 0.5:
                    last_ms = current_ms
                    self.get_play_status()
                    self.update_display()

                # check activity every 5 seconds
                if (current_ms - self.last_activity_check_ms) > 5:
                    self.last_activity_check_ms = current_ms
                    self.check_activity()

            except Exception as ex:
                print 'Error: an error occurred during execution: %s' % (ex)
                current_barcode = ""
                self.current_track = 0
                self.track_count = 0
        self.ser.close()


def main(argv):
    Jukebox4Kids().run()

if __name__ == "__main__":
    main(sys.argv[1:])

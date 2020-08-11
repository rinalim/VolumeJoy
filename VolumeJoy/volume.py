#!/usr/bin/python

import os, sys, struct, time, fcntl, termios, signal
import curses, errno, re
from pyudev import Context
from subprocess import *
from datetime import datetime

#    struct js_event {
#        __u32 time;     /* event timestamp in milliseconds */
#        __s16 value;    /* value */
#        __u8 type;      /* event type */
#        __u8 number;    /* axis/button number */
#    };

JS_MIN = -32768
JS_MAX = 32768
JS_REP = 0.20

JS_THRESH = 0.75

JS_EVENT_BUTTON = 0x01
JS_EVENT_AXIS = 0x02
JS_EVENT_INIT = 0x80

CONFIG_DIR = '/opt/retropie/configs/'
RETROARCH_CFG = CONFIG_DIR + 'all/retroarch.cfg'
PATH_VOLUMEJOY = '/opt/retropie/configs/all/VolumeJoy/'	

event_format = 'IhBB'
event_size = struct.calcsize(event_format)
js_fds = []
btn_up = -1
btn_down = -1
volume_step = [0,6,12,18,24,30,36,42,48,54,60,66,72,79,86,93,100]
TIMEOUT = 2
start_time = 0
audio_device = 'PCM'

def run_cmd(cmd):
    # runs whatever in the cmd variable
    p = Popen(cmd, shell=True, stdout=PIPE)
    output = p.communicate()[0]
    return output

def is_running(pname):
    ps_grep = run_cmd("ps -ef | grep " + pname + " | grep -v grep")
    if len(ps_grep) > 1 and "bash" not in ps_grep:
        return True
    else:
        return False

def kill_proc(name):
    ps_grep = run_cmd("ps -aux | grep " + name + "| grep -v 'grep'")
    if len(ps_grep) > 1: 
        os.system("killall " + name)

def signal_handler(signum, frame):
    close_fds(js_fds)
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def get_devices():
    devs = []
    if sys.argv[1] == '/dev/input/jsX':
        for dev in os.listdir('/dev/input'):
            if dev.startswith('js'):
                devs.append('/dev/input/' + dev)
    else:
        devs.append(sys.argv[1])

    return devs

def open_devices():
    devs = get_devices()

    fds = []
    for dev in devs:
        try:
            fds.append(os.open(dev, os.O_RDONLY | os.O_NONBLOCK ))
        except:
            pass

    return devs, fds

def close_fds(fds):
    for fd in fds:
        os.close(fd)

def read_event(fd):
    while True:
        try:
            event = os.read(fd, event_size)
        except OSError, e:
            if e.errno == errno.EWOULDBLOCK:
                return None
            return False

        else:
            return event

def process_event(event):
    global start_time

    (js_time, js_value, js_type, js_number) = struct.unpack(event_format, event)

    # ignore init events
    if js_type & JS_EVENT_INIT:
        return False

    if js_type == JS_EVENT_BUTTON and js_value == 1:
        #print "Button " + "number:" + str(js_number)
        #vol = int(run_cmd("amixer get PCM|grep -o [0-9]*%|sed 's/%//'"))
        #print vol

        read_vol = int(run_cmd("amixer get " + audio_device + " | grep -o [0-9]*%|sed 's/%//'"))
        if js_number == btn_down:
            if read_vol < 6:
                vol = 0
            else:
                vol = volume_step[read_vol/6-1]
            print "Decrease volume... " + str(vol)
        elif js_number == btn_up:
            if read_vol > 93:
                vol = 100
            else:
                vol = volume_step[read_vol/6+1]
            print "Increase volume... " + str(vol)
        else:
            return False
 
        #vol = int(run_cmd("amixer get PCM|grep -o [0-9]*%|sed 's/%//'"))
        run_cmd("amixer set "  + audio_device + " -- " + str(vol) + "%")
        start_time = datetime.now()
        os.system("echo " + PATH_VOLUMEJOY + "png/volume" + str(vol/6) + ".png > /tmp/volume.txt")
        if is_running("omxiv-volume") == False:
            os.system(PATH_VOLUMEJOY + "omxiv-volume " + PATH_VOLUMEJOY + "png/background.png -l 30001 -a center &")
            os.system(PATH_VOLUMEJOY + "omxiv-volume /tmp/volume.txt -f -t 5 -T blend --duration 20 -l 30002 -a center &")

    return True

def main():
    
    global btn_up, btn_down, start_time, audio_device
    
    cmd = run_cmd("amixer | grep Simple | sed 's/Simple mixer control //'")
    audio_device = cmd.split(',')[0].replace("'","")
    
    if os.path.isfile(PATH_VOLUMEJOY + "button.cfg") == False:
        return False

    f = open(PATH_VOLUMEJOY + "button.cfg", 'r')
    line = f.readline()
    words = line.split()
    btn_up = int(words[0])
    btn_down = int(words[1])

    js_fds=[]
    rescan_time = time.time()
    while True:
        do_sleep = True
        if not js_fds:
            js_devs, js_fds = open_devices()
            if js_fds:
                i = 0
                current = time.time()
                js_last = [None] * len(js_fds)
                for js in js_fds:
                    js_last[i] = current
                    i += 1
            else:
                time.sleep(1)
        else:
            i = 0
            for fd in js_fds:
                event = read_event(fd)
                if event:
                    do_sleep = False
                    if time.time() - js_last[i] > JS_REP:
                        if process_event(event):
                            js_last[i] = time.time()
                elif event == False:
                    close_fds(js_fds)
                    js_fds = []
                    break
                i += 1

        if time.time() - rescan_time > 2:
            rescan_time = time.time()
            if cmp(js_devs, get_devices()):
                close_fds(js_fds)
                js_fds = []

        if start_time != 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed >= TIMEOUT:
                kill_proc("omxiv-volume")
                start_time = 0

        if do_sleep:
            time.sleep(0.01)

if __name__ == "__main__":
    import sys

    try:
        main()

    # Catch all other non-exit errors
    except Exception as e:
        sys.stderr.write("Unexpected exception: %s" % e)
        sys.exit(1)

    # Catch the remaining exit errors
    except:
        sys.exit(0)

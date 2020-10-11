#!/usr/bin/python

import time, os
from subprocess import *
from datetime import datetime
import RPi.GPIO as GPIO

PATH_VOLUMEJOY="/opt/retropie/configs/all/VolumeJoy/"

volume_step = [0,6,12,18,24,30,36,42,48,54,60,66,72,79,86,93,100] 
TIMEOUT = 2
start_time = 0
audio_device = 'PCM'
upPin = 32
downPin = 36

GPIO.setmode(GPIO.BOARD)
GPIO.setup(upPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(downPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def buttonClicked(pin):
    global start_time
    read_vol = int(run_cmd("amixer get " + audio_device + " | grep -o [0-9]*%|sed 's/%//'"))
    if pin == downPin:
        if read_vol < 6:
            vol = 0
        else:
            vol = volume_step[read_vol/6-1]
        #print "Decrease volume... " + str(vol)
    elif pin == upPin:
        if read_vol > 93:
            vol = 100
        else:
            vol = volume_step[read_vol/6+1]
        #print "Increase volume... " + str(vol)
    run_cmd("amixer set "  + audio_device + " -- " + str(vol) + "%")
    start_time = datetime.now()
    os.system("echo " + PATH_VOLUMEJOY + "png/volume" + str(vol/6) + ".png > /tmp/volume.txt")
    if is_running("omxiv-volume") == False:
        os.system(PATH_VOLUMEJOY + "omxiv-volume " + PATH_VOLUMEJOY + "png/background.png -l 30001 -a center &")
        os.system(PATH_VOLUMEJOY + "omxiv-volume /tmp/volume.txt -f -t 5 -T blend --duration 20 -l 30002 -a center &")


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
    os.system("pkill " + name)

def Read(pin):
    adc=spi.xfer2([1,(8+pin)<<4,0])
    data=((adc[1]&3)<<8)+adc[2]
    return data

def InitVol(pin):
    read_vol = (1024-int(a_1))/10
    if read_vol > 100:
        read_vol = 100
    #print("amixer set " + audio_device + " -- " + str(volume_step[read_vol/6]) + "%")
    run_cmd("amixer set " + audio_device + " -- " + str(volume_step[read_vol/6]) + "%")
    return read_vol
 
def SetVol(vol):
    #print("amixer set " + audio_device + " -- " + str(volume_step[vol/6]) + "%")
    run_cmd("amixer set " + audio_device + " -- " + str(volume_step[vol/6]) + "%")
    os.system("echo " + PATH_VOLUMEJOY + "png/volume" + str(vol/6) + ".png > /tmp/volume.txt")
    if is_running("omxiv-volume") == False:
        os.system(PATH_VOLUMEJOY + "omxiv-volume " + PATH_VOLUMEJOY + "png/background.png -l 30001 -a center &")
        os.system(PATH_VOLUMEJOY + "omxiv-volume /tmp/volume.txt -f -t 5 -T blend --duration 20 -l 30002 -a center &")
    return vol

cmd = run_cmd("amixer | grep Simple | sed 's/Simple mixer control //'")
audio_device = cmd.split(',')[0].replace("'","")
# subscribe to button presses
GPIO.add_event_detect(upPin, GPIO.FALLING, callback=buttonClicked, bouncetime = 300)
GPIO.add_event_detect(downPin, GPIO.FALLING, callback=buttonClicked, bouncetime = 300)

while True :
    if start_time == 0:
        time.sleep(0.5)
    else:
        elapsed = (datetime.now() - start_time).total_seconds()
        if elapsed >= TIMEOUT:
            kill_proc("omxiv-volume")
            start_time = 0
        time.sleep(0.1)

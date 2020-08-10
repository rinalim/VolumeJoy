import time, os
import spidev
from subprocess import *
from datetime import datetime
import RPi.GPIO as GPIO

HOMEDIR="/opt/retropie/configs/all/VolumeJoy/"

spi=spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz=1000000

volume_step = [0,6,12,18,24,30,36,42,48,54,60,66,72,79,86,93,100] 
mcp3008=0 
TIMEOUT=2
shutdownPin = 5
# button debounce time in seconds
debounceSeconds = 0.01

GPIO.setmode(GPIO.BOARD)
GPIO.setup(shutdownPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def buttonStateChanged(pin):
    global buttonPressedTime

    if not (GPIO.input(pin)):
        # button is down
        if buttonPressedTime is None:
            buttonPressedTime = datetime.now()
    else:
        # button is up
        call(['shutdown', '-h', 'now'], shell=False)

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
    a_1 = Read(pin)
    read_vol = (1024-int(a_1))/10
    if read_vol > 100:
        read_vol = 100
    print("amixer set PCM -- " + str(volume_step[read_vol/6]) + "%")
    run_cmd("amixer set PCM -- " + str(read_vol) + "%")
    return read_vol
 
def SetVol(vol):
    print("amixer set PCM -- " + str(volume_step[vol/6]) + "%")
    run_cmd("amixer set PCM -- " + str(vol) + "%")
    os.system("echo " + HOMEDIR + "png/volume" + str(vol/6) + ".png > /tmp/volume.txt")
    if is_running("omxiv-volume") == False:
        os.system(HOMEDIR + "omxiv-volume " + HOMEDIR + "png/background.png -l 30001 -a center &")
        os.system(HOMEDIR + "omxiv-volume /tmp/volume.txt -f -t 5 -T blend --duration 20 -l 30002 -a center &")
    return vol

start_time = 0
cur_vol = InitVol(mcp3008)
# subscribe to button presses
GPIO.add_event_detect(shutdownPin, GPIO.BOTH, callback=buttonStateChanged)

while True :
    a_1 = Read(mcp3008)
    read_vol = (1024-int(a_1))/10
    if read_vol > 100:
        read_vol = 100
    if read_vol/6 != cur_vol/6:
        if read_vol-cur_vol != 1 and read_vol-cur_vol != -1:
            cur_vol = SetVol(read_vol)
            start_time = datetime.now()
 
    if start_time == 0:
        time.sleep(0.5)
    else:
        elapsed = (datetime.now() - start_time).total_seconds()
        if elapsed >= TIMEOUT:
            kill_proc("omxiv-volume")
            start_time = 0
        time.sleep(0.1)

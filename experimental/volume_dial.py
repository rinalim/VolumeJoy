import time, os
import spidev
from subprocess import *
from datetime import datetime

spi=spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz=1000000

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

def ReadAnalog(vol):
    adc=spi.xfer2([1,(8+vol)<<4,0])
    data=((adc[1]&3)<<8)+adc[2]
    return data

def SetVol(vol):
    print("amixer set PCM -- " + str(vol) + "%")
    run_cmd("amixer set PCM -- " + str(vol) + "%")
    kill_proc("pngvolume")
    os.system("echo ./png/volume" + str(vol/6) + ".png > /tmp/volume.txt")
    if is_running("omxiv") == False:
        os.system("./omxiv /tmp/volume.txt -f -t 5 -T blend --duration 20 -l 30002 -a center &")

mcp3008=0     
cur_vol = int(run_cmd("amixer get PCM|grep -o [0-9]*%|sed 's/%//'"))
start_time = 0
while True :
    a_1 = ReadAnalog(mcp3008)
    #print('readvol : ' , a_1 , 'Voltage:' , 3.3*a_1/1024 )
    read_vol = (1024-int(a_1))/10
    if read_vol > 100:
        read_vol = 100
    if read_vol - cur_vol > 2 or read_vol - cur_vol < -2:
        SetVol(read_vol)
        start_time = datetime.now()
        cur_vol = read_vol
 
    if start_time == 0:
        time.sleep(0.5)
    else:
        elapsed = (datetime.now() - start_time).total_seconds()
        if elapsed >= 3:
            kill_proc("omxiv")
            start_time = 0
        time.sleep(0.1)

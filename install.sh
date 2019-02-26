sudo cp ./libraspidmx.so.1 /usr/lib

mkdir /opt/retropie/configs/all/VolumeJoy/
cp -f -r ./VolumeJoy /opt/retropie/configs/all/

sudo chmod 755 /opt/retropie/configs/all/VolumeJoy/pngvolume

sudo sed -i '/volume.py/d' /opt/retropie/configs/all/runcommand-onstart.sh
echo 'python /opt/retropie/configs/all/VolumeJoy/volume.py /dev/input/js0 &' >> /opt/retropie/configs/all/runcommand-onstart.sh

echo 'Install Completed'

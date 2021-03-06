## install.sh
# Install      :
# cd /home/pi
# git clone https://github.com/rinalim/VolumeJoy
# cd VolumeJoy
# chmod 755 install.sh
# sudo ./install.sh
#
# Reference    :
# https://github.com/RetroPie/RetroPie-Setup/blob/master/scriptmodules/supplementary/runcommand/joy2key.py
# https://github.com/sana2dang/PauseMode

sudo apt install python-pyudev -y

rm -rf /opt/retropie/configs/all/VolumeJoy/
mkdir /opt/retropie/configs/all/VolumeJoy/
cp -f -r ./VolumeJoy /opt/retropie/configs/all/

sudo chmod 755 /opt/retropie/configs/all/VolumeJoy/omxiv-volume

sudo sed -i '/VolumeJoy/d' /opt/retropie/configs/all/autostart.sh
sudo sed -i '1i\\/usr/bin/python /opt/retropie/configs/all/VolumeJoy/volume_gpio.py &' /opt/retropie/configs/all/autostart.sh

echo
echo "Setup Completed. Reboot after 3 Seconds."
sleep 3
reboot

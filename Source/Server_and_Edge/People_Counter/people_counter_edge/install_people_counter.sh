#!/bin/bash

echo "Run this script with SUDO!!!!"

#Getting needed Resources
echo -n "Installing needed Resources..."
sudo apt-get update
sudo apt-get install python3-pip -y
sudo apt-get install python3-opencv -y
sudo apt-get install python3-pip -y
sudo pip install influxdb-client
sudo apt-get install python3-paho-mqtt -y
sudo apt-get install python3-yaml -y
echo "...DONE"

#Creating Folders
echo .
echo .
echo -n "Creating folders..."
sudo mkdir /etc/people-counter-client
sudo mkdir /etc/people-counter-client/ssl
sudo mkdir /opt/people-counter-client
sudo mkdir /var/log/people-counter-client
echo -n "...DONE"

#Copying Files
echo .
echo.
echo -n "Copying files ..."
sudo cp *.py /opt/people-counter-client/
sudo cp *.yaml /etc/people-counter-client/
sudo cp people-counter-client.service /lib/systemd/system/
echo ".. DONE"

#Installing Service
echo .
echo .
echo -n "Creating takePicture-Service ..."
sudo chmod 644 /lib/systemd/system/people-counter-client.service
sudo systemctl daemon-reload
sudo systemctl enable people-counter-client.service
echo "..DONE"

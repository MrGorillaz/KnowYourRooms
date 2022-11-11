#!/bin/bash

echo "Run this script with SUDO!!!!"

#Getting needed Resources
echo -n "Installing needed Resources..."
sudo apt-get update
sudo apt-get install python3-pip -y
sudo apt-get install python3-opencv -y
sudo apt-get install python3-pip -y
sudo apt-get install python3-yaml -y
sudo apt-get install python3-flask -y
sudo apt-get install python3-pil -y

echo "...DONE"

#Creating Folders
echo .
echo .
echo -n "Creating folders..."
sudo mkdir /etc/people-counter-server
sudo mkdir /etc/people-counter-server/ssl
sudo mkdir /etc/people-counter-server/docker_temp
sudo mkdir /etc/people-counter-server/models
sudo mkdir /opt/people-counter-server
sudo mkdir /var/log/people-counter-server
echo -n "...DONE"

#Copying Files
echo .
echo.
echo -n "Copying files ..."
sudo cp *.py /opt/people-counter-server/
sudo cp *.yaml /etc/people-counter-server/
sudo cp people-counter-server.service /lib/systemd/system/
echo ".. DONE"

#Installing Service
echo .
echo .
echo -n "Creating takePicture-Service ..."
sudo chmod 644 /lib/systemd/system/people-counter-server.service
sudo systemctl daemon-reload
sudo systemctl enable people-counter-server.service
echo "..DONE"

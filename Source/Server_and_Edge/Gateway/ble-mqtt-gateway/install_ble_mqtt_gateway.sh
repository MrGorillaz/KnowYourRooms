#!/bin/bash

echo "Run this script with SUDO!!!!"

#Getting needed Resources
echo -n "Installing needed Resources..."
sudo apt-get update
sudo apt-get install python3-pip -y
sudo pip install influxdb-client
sudo apt-get install python3-paho-mqtt -y
sudo apt-get install python3-yaml -y
echo "...DONE"

#Creating Folders
echo .
echo .
echo -n "Creating folders..."
sudo mkdir /etc/ble-mqtt-gateway
sudo mkdir /etc/ble-mqtt-gateway/ssl
sudo mkdir /opt/ble-mqtt-gateway
sudo mkdir /var/log/ble-mqtt-gateway
echo -n "...DONE"

#Copying Files
echo .
echo .
echo -n "Copying files ..."
sudo cp *.py /opt/ble-mqtt-gateway/
sudo cp *.yaml /etc/ble-mqtt-gateway/
sudo cp ble-mqtt-gateway.service /lib/systemd/system/
echo ".. DONE"

#Installing Service
echo .
echo .
echo -n "Creating takePicture-Service ..."
sudo chmod 644 /lib/systemd/system/ble-mqtt-gateway.service
sudo systemctl daemon-reload
sudo systemctl enable ble-mqtt-gateway.service
echo "..DONE"

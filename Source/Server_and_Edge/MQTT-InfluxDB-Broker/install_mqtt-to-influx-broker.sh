#!/bin/bash

echo "Run this script with SUDO!!!!"

#Getting needed Resources
echo -n "Installing needed Resources..."
#wget -qO- https://repos.influxdata.com/influxdb.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdb.gpg > /dev/null
#export DISTRIB_ID=$(lsb_release -si); export DISTRIB_CODENAME=$(lsb_release -sc)
#echo "deb [signed-by=/etc/apt/trusted.gpg.d/influxdb.gpg] https://repos.influxdata.com/${DISTRIB_ID,,} ${DISTRIB_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/influxdb.list > /dev/null
curl -sL https://repos.influxdata.com/influxdb.key | apt-key add -
source /etc/os-release
test $VERSION_ID = "7" && echo "deb https://repos.influxdata.com/debian wheezy stable" | tee -a /etc/apt/sources.list
test $VERSION_ID = "8" && echo "deb https://repos.influxdata.com/debian jessie stable" | tee -a /etc/apt/sources.list
sudo apt-get update && sudo apt-get install influxdb2 -y
sudo apt-get install mosquitto -y
sudo apt-get install python3-pip -y
sudo pip install influxdb-client
sudo apt-get install python3-paho-mqtt -y
sudo apt-get install python3-yaml -y
echo "...DONE"

#Creating Folders
echo .
echo .
echo -n "Creating folders..."
sudo mkdir /etc/mqtt-to-influx-broker
sudo mkdir /etc/mqtt-to-influx-broker/ssl
sudo mkdir /opt/mqtt-to-influx-broker
sudo mkdir /var/log/mqtt-to-influx-broker
echo -n "...DONE"

#Copying Files
echo .
echo .
echo -n "Copying files ..."
sudo cp *.py /opt/mqtt-to-influx-broker/
sudo cp *.yaml /etc/mqtt-to-influx-broker/
sudo cp mqtt-to-influx-broker.service /lib/systemd/system/
echo ".. DONE"

#Installing Service
echo .
echo .
echo -n "Creating mqtt-to-influx-broker-Service ..."
sudo chmod 644 /lib/systemd/system/mqtt-to-influx-broker.service
sudo systemctl daemon-reload
sudo systemctl enable mqtt-to-influx-broker.service
echo "..DONE"

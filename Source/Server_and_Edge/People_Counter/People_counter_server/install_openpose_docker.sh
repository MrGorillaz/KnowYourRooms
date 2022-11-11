#!/bin/bash
sudo apt-get install docker.io -y
sudo docker build . -f dockerfile -t "openpose"
sudo groupadd docker
echo "Enter Username to upgrade user to Docker Group:"
read username
sudo usermod -aG docker $username

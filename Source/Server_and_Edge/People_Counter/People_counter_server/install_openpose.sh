#!/bin/bash
sudo apt-get install python3-dev -y
sudo apt-get install cmake -y
sudo apt-get install libopencv-dev -y
sudo pip3 install numpy opencv-python
sudo git clone https://github.com/CMU-Perceptual-Computing-Lab/openpose
cd openpose/
sudo git submodule update --init --recursive --remote
sudo mkdir build/
sudo /bin/bash  scripts/ubuntu/install_deps.sh
cd build/
sudo cmake -DGPU_MODE:String=CPU_ONLY -DDOWNLOAD_BODY_MPI_MODEL:Bool=ON -DDOWNLOAD_BODY_COCO_MODEL:Bool=ON -DDOWNLOAD_FACE_MODEL:Bool=ON -DDOWNLOAD_HAND_MODEL:Bool=ON -DUSE_PYTHON_INCLUDE_DIR=ON -DBUILD_PYTHON=ON -DPYTHON_EXECUTABLE=/usr/bin/python3 ..
sudo make
sudo make install

#!/bin/bash

sudo sed -i "/#\$nrconf{restart} = 'i';/s/.*/\$nrconf{restart} = 'a';/" /etc/needrestart/needrestart.conf
sudo apt update
sudo apt install -qq -y python3-pip
./py-help.sh -m pip install -r requirements.txt --ignore-installed

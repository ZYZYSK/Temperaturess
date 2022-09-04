#!/bin/bash

# delete files if exists
if [ -d /opt/Temperaturess ]; then
    rm -r /opt/Temperaturess
fi
# copy files
cd ../
cp -r Temperaturess /opt
cd /opt/Temperaturess
echo "current directory: "+`pwd`

# create virtualenv
pip install virtualenv
python -m virtualenv venv_temperaturess
# enable virtualenv
source venv_temperaturess/bin/activate
# install libraries
sudo apt install libglib2.0-dev
pip install --upgrade pip
pip install numpy
pip install plotly
pip install matplotlib
pip install git+https://github.com/AmbientDataInc/ambient-python-lib.git
pip install bluepy
pip install uwsgi

# crontab
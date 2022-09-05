#!/bin/bash

echo "current directory: "+`pwd`

# create virtualenv
cd ${HOME}/Temperaturess
pip install virtualenv
python -m virtualenv venv_temperaturess
# enable virtualenv
source venv_temperaturess/bin/activate
# install libraries
sudo apt install libglib2.0-dev
pip install --upgrade pip
pip install django
pip install numpy
pip install plotly
pip install matplotlib
pip install git+https://github.com/AmbientDataInc/ambient-python-lib.git
pip install bluepy
pip install uwsgi

# crontab
echo "*/5 * * * * cd ${HOME}/Temperaturess; source venv_temperaturess/bin/activate; venv_temperatures/bin/python3 temperaturess/manage.py inkbird" > crontab.txt
crontab crontab.txt
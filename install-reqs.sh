#! /bin/bash
# Installs al required modules

############### Python RTMidi
pip install Cython

git clone https://github.com/SpotlightKid/python-rtmidi.git
cd python-rtmidi
git submodule update --init
python setup.py install --no-jack
cd ..
rm -rf python-rtmidi
###################################################

############### Everything else
pip3 install -r requirements.txt

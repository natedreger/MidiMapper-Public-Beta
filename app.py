# app.py

###############################
# MIDI mapping app with web interface
# Dependencies :
# web_interface.py
# midi_mapper.py
# prope_ports.py
# midioutwrapper.py
# settings.json
# keymap.json

import os
import sys
import json
from dotenv import load_dotenv
from multiprocessing import Process

from web_interface import server_main
from midi_mapper import midi_main

sys.path.insert(0, os.path.dirname(__file__))
load_dotenv('.env')
SETTINGS_FILE=os.environ.get('SETTINGS_FILE')

p1 = Process(target=server_main, args=(SETTINGS_FILE,))
p2 = Process(target=midi_main, args=(SETTINGS_FILE,))

p1.start()
p2.start()

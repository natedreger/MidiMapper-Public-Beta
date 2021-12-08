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
import time
import socketio
from dotenv import load_dotenv
from multiprocessing import Process

from web_interface import server_main
from midi_mapper import midi_main

sys.path.insert(0, os.path.dirname(__file__))
load_dotenv('.env')
SETTINGS_FILE=os.environ.get('SETTINGS_FILE')

file = open(SETTINGS_FILE)
settings = json.loads(file.read())
server_port = settings['socket_port']
server_addr = 'localhost'

sio2 = socketio.Client()

@sio2.event
def connect():
    print('[INFO] App Successfully connected to server.')

@sio2.on('apply_settings')
def restart_midi():
    print('restarting_midi')
    p1.kill()
    p2.kill()
    time.sleep(3)
    p1.start()
    p2.start()

@sio2.on('restart_server')
def restart_server():
    print('restarting_server')
    p2.terminate()
    time.sleep(3)
    p2.start()


p1 = Process(target=server_main, args=(SETTINGS_FILE,))
p2 = Process(target=midi_main, args=(SETTINGS_FILE,))

try:
    p1.start()
    p2.start()
    sio2.connect(f'http://{server_addr}:{server_port}')
except:
    print('Processes Terminated')
    p1.terminate()
    p2.terminate()

#!/usr/bin/env python3
# app.py

###############################
# MIDI mapping app with web interface
# Dependencies :
# web_interface.py
# midi_mapper.py
# probe_ports.py
# midioutwrapper.py
# globals.py
# settings.json
# keymap.json

import gc
import os
import json
import time
import socketio
from multiprocessing import Process

from web_interface import server_main
from midi_mapper import midi_main, end_MIDI
from osc import osc_main
from logger import *
from globals import owner, VERSION, SETTINGS_FILE, read_settings

logs.debug(f'app.py running as PID: {os.getpid()} as User: {owner(os.getpid())}')

midi_processes = []
server_processes = []
osc_processes = []

settings = read_settings(SETTINGS_FILE)#json.loads(file.read())
server_port = settings['socket_port']
server_addr = 'localhost'

sio2 = socketio.Client()

@sio2.event
def connect():
    print('[INFO] App Successfully connected to server.')

@sio2.on('restart_midi')
def restart_midi():
    print('Restarting MIDI')
    time.sleep(0.1)
    for midi_process in midi_processes:
        midi_process.terminate()
    midi_processes.append(Process(target=midi_main, args=(SETTINGS_FILE,)))
    next_midi = len(midi_processes)-1
    time.sleep(0.1)
    midi_processes[next_midi].start()
    # sio2.emit('midi_restarted')
    print('MIDI Restarted')
    logs.info('MIDI Restarted')

@sio2.on('restart_server')
def restart_server():
    print('Restarting Server')
    load_settings()
    time.sleep(1.0)
    for server_process in server_processes:
        server_process.terminate()
    server_processes.append(Process(target=server_main, args=(SETTINGS_FILE,)))
    next_server = len(server_processes)-1
    server_processes[next_server].start()
    restart_midi()
    print('Server Restarted')
    logs.info('Server Restarted')

@sio2.on('quit')
def quit():
    end_MIDI()
    time.sleep(1.0)
    print('Exiting')
    terminateProcesses()
    time.sleep(1.0)
    logs.info(f"{__name__} quit")
    os._exit(os.EX_OK)

@sio2.on('reboot')
def reboot():
    print('Rebooting')
    terminateProcesses()
    time.sleep(1.0)
    os.system("sudo reboot now")

@sio2.on('shutdown')
def reboot():
    print('Shutting Down')
    terminateProcesses()
    time.sleep(1.0)
    os.system("sudo shutdown now")

def load_settings():
    global settings, server_port, server_addr
    # file = open(SETTINGS_FILE)
    settings = read_settings(SETTINGS_FILE)#json.loads(file.read())
    server_port = settings['socket_port']
    server_addr = 'localhost'

def terminateProcesses():
    for server_process in server_processes:
        server_process.terminate()
    for midi_process in midi_processes:
        midi_process.terminate()
    for osc_process in osc_processes:
        osc_process.terminate()
    gc.collect()

load_settings()

# Create initial MIDI and server processes
midi_processes.append(Process(target=midi_main, args=(SETTINGS_FILE,)))
server_processes.append(Process(target=server_main, args=(SETTINGS_FILE,)))
osc_processes.append(Process(target=osc_main, args=(settings,)))

logs.info(f"{__name__} started")

try:
    for server_process in server_processes:
        server_process.start()
    for midi_process in midi_processes:
        midi_process.start()
    for osc_process in osc_processes:
        osc_process.start()

    connected = False
    while not connected:
        try:
            sio2.connect(f'http://{server_addr}:{server_port}')
        except Exception as err:
            print("ConnectionError: %s", err)
            logs.error(f"{__name__} - {err}")
        else:
            print("Connected!")
            connected = True
except:
    terminateProcesses()
    print('Processes Terminated')

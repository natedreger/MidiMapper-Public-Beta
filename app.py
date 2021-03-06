#! ./venv/bin/python3
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
import threading
from multiprocessing import Process
from subprocess import Popen, PIPE, STDOUT

# import modules.streamDeckHandler
from globals import owner, VERSION, SETTINGS_FILE, settingsCLASS, ledQueue, streamDeckQueue
from modules.logger import *
from web_interface import server_main
from midi_mapper import midi_main, end_MIDI
from osc import osc_main
from mqttPubSub import *
from modules.ledControl import *

logs.debug(f'app.py running as PID: {os.getpid()} as User: {owner(os.getpid())}')

midi_processes = []
server_processes = []

settings = settingsCLASS.config
server_port = settingsCLASS.socket_port
server_addr = 'localhost'

sio2 = socketio.Client()

@sio2.event
def connect():
    print('[INFO] App Successfully connected to server.')

@sio2.on('restart_midi')
def restart_midi(data):
    ledQueue.put("led1.pulseSlow('yellow')")
    print('Restarting MIDI')
    time.sleep(0.1)
    for midi_process in midi_processes:
        midi_process.terminate()
    midi_processes.append(Process(target=midi_main))
    next_midi = len(midi_processes)-1
    time.sleep(0.1)
    midi_processes[next_midi].start()
    # sio2.emit('midi_restarted')
    print('MIDI Restarted')
    logs.info('MIDI Restarted')

@sio2.on('restart_server')
def restart_server():
    ledQueue.put("led1.pulseSlow('yellow')")
    print('Restarting Server')
    load_settings()
    time.sleep(1.0)
    for server_process in server_processes:
        server_process.terminate()
    server_processes.append(Process(target=server_main, args=(SETTINGS_FILE,)))
    next_server = len(server_processes)-1
    server_processes[next_server].start()
    restart_midi(True)
    print('Server Restarted')
    logs.info('Server Restarted')

@sio2.on('quit')
def quit():
    ledQueue.put("led1.pulseFast('magenta')")
    end_MIDI()
    time.sleep(1.0)
    print('Exiting')
    ledQueue.put("led1.off()")
    terminateProcesses()
    time.sleep(1.0)
    logs.info(f"{__name__} quit")
    os._exit(os.EX_OK)

@sio2.on('reboot')
def reboot(pwd):
    print('Rebooting')
    terminateProcesses()
    time.sleep(1.0)
    # os.system("shutdown /r /t 0")
    # os.system("sudo reboot now")

@sio2.on('shutdown')
def shutdown(pwd):
    print('Shutting Down')
    terminateProcesses()
    time.sleep(1.0)
    # os.system("shutdown /s /t 0")
    # os.system("sudo shutdown now")

def load_settings():
    global settings, server_port, server_addr
    settings = settingsCLASS.config
    server_port = settingsCLASS.socket_port
    server_addr = 'localhost'

def stop(self):
    self.stopped = True

def terminateProcesses():
    for server_process in server_processes:
        server_process.terminate()
    for midi_process in midi_processes:
        midi_process.terminate()
    osc_process.terminate()
    # streamdeck.terminate()
    gc.collect()

# def runStreamDeck():
#     CommandData = ''
#     script_path = './streamdeck_cli/streamdeck-cli.py'
#     p = Popen([sys.executable, '-u', script_path, '-n'], stdout=PIPE, stderr=PIPE)
#     with p.stdout:
#         for line in iter(p.stdout.readline, b''):
#             try:
#                 CommandData = json.loads(line.decode())
#                 print('StreamDeck Data')
#                 streamDeckQueue.put(CommandData)
#             except: pass
#     p.wait()


load_settings()

# Create initial MIDI and server processes
ledThread = threading.Thread(target=ledQueueHandler)
midi_processes.append(Process(target=midi_main,))
server_processes.append(Process(target=server_main, args=(SETTINGS_FILE,)))
osc_process = Process(target=osc_main, args=(settings,))
# streamdeck = Process(target=runStreamDeck)


logs.info(f"{__name__} started")

try:
    ledThread.start()
    osc_process.start()
    # streamdeck.start()
    for server_process in server_processes:
        server_process.start()
    for midi_process in midi_processes:
        midi_process.start()

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
except KeyboardInterrupt:
    print('Processes Terminating')
    quit()

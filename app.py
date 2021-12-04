#!/usr/bin/env python
#
# https://github.com/SpotlightKid/python-rtmidi
# https://python-osc.readthedocs.io
# app.py

import logging
import sys
import time
import json
import queue

from pythonosc import udp_client

from rtmidi import (MidiIn, MidiOut)
from rtmidi.midiutil import open_midioutput, open_midiinput

### Local Modules
from midioutwrapper import MidiOutWrapper
from probe_ports import probe_ports, getAvailableIO


from threading import Lock
from flask import Flask, render_template, session, request, \
    copy_current_request_context
from flask_socketio import SocketIO, emit, disconnect


# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

keyMapFile = 'keymap.json'
settingsFile = 'settings.json'
# Default out ports
outport = 0#None

# globals
mappedkeys = []
indevice = ""
outdevice = ""

q = queue.Queue()

outports = []#getAvailableIO(MidiOut)
inports = getAvailableIO(MidiIn)

print(f'{len(inports)} available inputs')

class MidiInput:
    def handle_midi_in(self, event, data):
        message, deltatime = event
        q.put([self.device, message])

    def close_MidiInput(self):
        self.mi.close_port()

    def delete_MidiInput(self):
        self.mi.delete()

    def __init__(self, pn, q):
        self.pn=pn
        self.q = q
        self.mi = open_midiinput(pn)
        self.mi = self.mi[0]
        self.mi.ignore_types(sysex=False, timing=True, active_sense=True)
        self.device = self.mi.get_port_name(pn, encoding=u'auto').split(':')[0]
        self.mi.set_callback(self.handle_midi_in)

# functions
def searchKeyMap(device, note, exact):
    print(f'searching keymap for note {note} on {device}')
    for key in mappedkeys:
        if exact:
            device = device
        else:
            device = key['device']
            if (str(key['note']) == str(note)) and (key['device'] == device):
                return key

def loadKeyMap():
    global keyMapFile
    keyMapFile = settings["keymap"]
    file = open(keyMapFile)
    map = json.loads(file.read())
    file.close()
    return map

def getMappedKeys():
    global mappedkeys
    tempKeys = loadKeyMap()
    mappedkeys = tempKeys
    return mappedkeys

def setOutput(port):
    global outport
    midiout.close_port()
    midiout.open_port(port)
    outport = port
    # emit('outport', {'data': 'Connected', 'port': port, 'outports':outports})

def load_settings():
    global settings
    file = open(settingsFile)
    settings = json.loads(file.read())
    print(settings)
    file.close()

def save_settings():
    file = open(settingsFile)
    settings['last_output'] = outport
    settings['last_keymap'] = keyMapFile
    print(settings)
    file.close()

### Flask
@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode, availableInputs=inports, availableOutputs=outports, activeOutput=outport)


# recieve emit events
@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})

@socketio.event
def webMidiNoteIn(message):
    ch = int(message['data'][0])+143
    note = int(message['data'][1])
    q.put(['Web Interface Note', [ch, note, 1]])

@socketio.event
def webPCIn(message):
    ch = int(message['data'][0])
    pc = int(message['data'][1])
    # emit('my_response', {'data': message['data']})
    mw = MidiOutWrapper(midiout, ch=ch)
    mw.send_program_change(pc)
    print(f'PC sent channel: {ch} value: {pc}')
    socketio.emit('midi_sent', {'data': f'PC channel: {ch} value: {pc}'})

@socketio.event
def select_io(message):
    # inport = int(message['data'][0])
    global outport
    outport = int(message['data'][1])
    setOutput(outport)
    socketio.emit('outport', {'data': 'Connected', 'port': outport, 'outports':outports})
    emit('my_response', {'data': message['data']})

# recieve broadcast event
@socketio.event
def my_broadcast_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)

@socketio.event
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(midiInput_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})
    emit('outport', {'data': 'Connected', 'port': outport, 'outports':outports})


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', request.sid)

def midiInput_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    try:
        while True:
            msg = q.get(1)
            if msg:
                indevice = msg[0]
                message = msg[1]
                print("[%s] %r" % (indevice, message))
                channel=message[0]-143
                note=message[1]
                velocity=message[2]
                if velocity > 0:
                    socketio.emit('midi_msg', {'data': f'{msg}'})
                    remap = searchKeyMap(indevice, note, False)
                    if remap:
                        if remap['type'] == 'PC':
                            mw = MidiOutWrapper(midiout, ch=remap['channel'])
                            mw.send_program_change(remap['value'])
                            print(f"PC sent channel: {remap['channel']} value: {remap['value']}")
                            socketio.emit('midi_sent', {'data': f"Mapped to PC channel: {remap['channel']} value: {remap['value']}"})
                        elif remap['type'] == 'NOTE_ON':
                            mw = MidiOutWrapper(midiout, ch=remap['channel'])
                            mw.send_note_on(remap['new_note'])
                            print(f"sent NOTE_ON {remap['new_note']}")
                            socketio.emit('midi_sent', {'data': f"Mapped to NOTE_ON Channel: {remap['channel']} Note: {remap['new_note']}"})
                        elif remap['type'] == 'OSC':
                            OSC_client = udp_client.SimpleUDPClient(remap['host'], remap['port'])
                            OSC_client.send_message(remap['message'],'')
                            print(f'OSC message {remap["message"]}')
                            socketio.emit('midi_sent', {'data': f"Mapped to OSC message {remap['message']}"})
                    else:
                        mw = MidiOutWrapper(midiout, ch=channel)
                        mw.send_note_on(note)
                        print(f'sent {note}')
                        socketio.emit('midi_sent', {'data': f'Channel: {channel} Note: {note}'})
    except KeyboardInterrupt:
        print('')
    finally:
        print("Exit.")
        for i in range (0, len(inports)):
            x = f'm{i}'
            globals()[x].close_MidiInput()
            del globals()[x]
        midiout.close_port()
        sys.exit()

######### Setup #############

load_settings()
# Dynamicly open midi inputs
try:
    for i in range (0, len(inports)):
        x = f'm{i}'
        globals()[x] = MidiInput(i, q)

    midiout, outport_name = open_midioutput(outport)
    temp = midiout.get_ports()
    for o in temp:
        outports.append(o.split(':')[0])
    setOutput(settings['last_output'])
    getMappedKeys()

    # print(f'output: {outdevice}')
    # print(f'Key Map {mappedkeys}')

except (EOFError, KeyboardInterrupt):
    print("Exit.")
    sys.exit()


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5005)

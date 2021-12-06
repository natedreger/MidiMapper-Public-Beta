#!/usr/bin/env python
#
# https://github.com/SpotlightKid/python-rtmidi
# https://python-osc.readthedocs.io
# https://stackoverflow.com/questions/43861164/passing-data-between-separately-running-python-scripts
# midi_test.py
#


import logging
import sys
import time
import json
from multiprocessing import Process,Queue,Pipe
import queue

from pythonosc import udp_client

from rtmidi import MidiIn, MidiOut
from rtmidi.midiutil import open_midioutput, open_midiinput

### Local Modules
from midioutwrapper import MidiOutWrapper
from probe_ports import probe_ports, getAvailableIO

# log = logging.getLogger('midiout')
# logging.basicConfig(level=logging.DEBUG)

keyMapFile = 'keymap.json'
settingsFile = 'settings.json'
# Default out ports
outport = 6 # None

# globals
mappedkeys = []
indevice = ""
outdevice = ""

outports = []#getAvailableIO(MidiOut)
inports = getAvailableIO(MidiIn)

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
    mapfile = open(keyMapFile)
    map = json.loads(mapfile.read())
    mapfile.close()
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

class MidiInput:
    def handle_midi_in(self, event, data):
        message, deltatime = event
        q.put([self.device, message])
    def close_MidiInput(self):
        self.mi.close_port()
        #self.mi.delete()

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


q = queue.Queue()
# probe_ports()
inports = getAvailableIO(MidiIn)
# print(f'{len(inports)} available inputs')

# initial setup
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

# main loop
print("Entering main loop. Press Control-C to exit.")

try:
    timer = time.time()
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
                # child_conn.send('midi_msg', {'data': f'{msg}'})
                remap = searchKeyMap(indevice, note, False)
                if remap:
                    if remap['type'] == 'PC':
                        mw = MidiOutWrapper(midiout, ch=remap['channel'])
                        mw.send_program_change(remap['value'])
                        print(f"PC sent channel: {remap['channel']} value: {remap['value']}")
                        # child_conn.send('midi_sent', {'data': f"Mapped to PC channel: {remap['channel']} value: {remap['value']}"})
                    elif remap['type'] == 'NOTE_ON':
                        mw = MidiOutWrapper(midiout, ch=remap['channel'])
                        mw.send_note_on(remap['new_note'])
                        print(f"sent NOTE_ON {remap['new_note']}")
                        # child_conn.send('midi_sent', {'data': f"Mapped to NOTE_ON Channel: {remap['channel']} Note: {remap['new_note']}"})
                    elif remap['type'] == 'OSC':
                        OSC_client = udp_client.SimpleUDPClient(remap['host'], remap['port'])
                        OSC_client.send_message(remap['message'],'')
                        print(f'OSC message {remap["message"]}')
                        # child_conn.send('midi_sent', {'data': f"Mapped to OSC message {remap['message']}"})
                else:
                    mw = MidiOutWrapper(midiout, ch=channel)
                    mw.send_note_on(note)
                    print(f'sent {note}')
                    # child_conn.send('midi_sent', {'data': f'Channel: {channel} Note: {note}'})
                time.sleep(0.1)

        time.sleep(0.01)
except KeyboardInterrupt:
    print('')
finally:
    for i in range (0, len(inports)):
        x = f'm{i}'
        globals()[x].close_MidiInput()
        del globals()[x]
    midiout.close_port()
    print("Exiting app.")
    sys.exit()

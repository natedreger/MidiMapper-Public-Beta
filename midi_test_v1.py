#!/usr/bin/env python
#
# https://github.com/SpotlightKid/python-rtmidi
# midi_test.py
#

from __future__ import print_function

import logging
import sys
import time
import json
import mido

from pythonosc import udp_client

from midioutwrapper import MidiOutWrapper
from probe_ports import probe_ports

from rtmidi.midiutil import open_midioutput, open_midiinput


# log = logging.getLogger('midiout')
# logging.basicConfig(level=logging.DEBUG)

keyMapFile = 'keymap.json'
# Default in and out ports
outport = 3 # None
inport = 1 #None

# globals
mappedkeys = []
indevice = ""
outdevice = ""

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

# initial setup

probe_ports()
try:
    midiin, inport_name = open_midiinput(inport)
    indevice = inport_name.split(':')[0]
    midiout, outport_name = open_midioutput(outport)
    outdevice = outport_name.split(':')[0]
    getMappedKeys()

    print(f'input: {indevice}')
    print(f'output: {outdevice}')
    print(f'Key Map {mappedkeys}')

except (EOFError, KeyboardInterrupt):
    sys.exit()

# main loop
print("Entering main loop. Press Control-C to exit.")

try:
    timer = time.time()
    while True:
        msg = midiin.get_message()

        if msg:
            message, deltatime = msg
            timer += deltatime
            print("[%s] @%0.6f %r" % (indevice, timer, message))
            note=message[1]
            velocity=message[2]
            if note > 0 and velocity > 0:
                remap = searchKeyMap(indevice, note, False)
                print(remap)
                if remap:
                    if remap['type'] == 'PC':
                        mw = MidiOutWrapper(midiout, ch=remap['channel'])
                        mw.send_program_change(remap['value'])
                    elif remap['type'] == 'OSC':
                        client = udp_client.SimpleUDPClient(remap['host'], remap['port'])
                        client.send_message(remap['message'],'')
                        print(f'OSC message {remap["message"]}')
                else:
                    mw = MidiOutWrapper(midiout)
                    mw.send_note_on(note)
                    print(f'sent {note}')
                time.sleep(0.1)

        time.sleep(0.01)
except KeyboardInterrupt:
    print('')
finally:
    print("Exit.")
    midiin.close_port()
    midiout.close_port()
    del midiin
    del midiout

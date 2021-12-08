#!/usr/bin/env python
#
# https://github.com/SpotlightKid/python-rtmidi
# https://python-osc.readthedocs.io
# midi_mapper.py
#


import logging
import sys
import time
import json
import queue
import socketio
import gc

from pythonosc import udp_client

from rtmidi import MidiIn, MidiOut
from rtmidi.midiutil import open_midioutput, open_midiinput

### Local Modules
from midioutwrapper import MidiOutWrapper
from probe_ports import probe_ports, getAvailableIO

# log = logging.getLogger('midiout')
# logging.basicConfig(level=logging.DEBUG)

# keyMapFile = 'keymap.json'
# settingsFile = 'settings.json'
# Default out ports
outport = 0

# globals
mappedkeys = []
filterInput = []
ignoreInputs = []
ignoreOutputs = []
filteredOutputList = []
filteredInputList = []
message_buffer = []
indevice = ""
outdevice = ""
activeInput = []
activeOutput = ""

outports = []
inports = getAvailableIO(MidiIn)
# global_vars = ['m0','m1','m2']

q = queue.Queue()

sio = socketio.Client()
server_addr = 'localhost'
server_port = '5005'

################ socket IO #######################3
@sio.event
def connect():
    send_settings()
    print('[INFO] MIDI Successfully connected to server.')

@sio.event
def connect_error():
    print('[INFO] Failed to connect to server.')

@sio.event
def disconnect():
    print('[INFO] Disconnected from server.')

@sio.on('server_msg')
def handle_server_message(message):
    print(message)

@sio.on('webMidiNoteIn')
def webMidiNoteIn(message):
    ch = int(message['data'][0])+143
    note = int(message['data'][1])
    indevice = 'Web Interface'
    filter = ('All' in filterInput) or (indevice in filterInput)
    if filter:
        q.put(['Web Interface', [ch, note, 1]])
        sio.emit('midi_sent', {'data': f'MIDI channel: {ch} value: {note}'})
    else:
        send_ignore(indevice)

@sio.on('webPCIn')
def webPCIn(message):
    ch = int(message['data'][0])
    pc = int(message['data'][1])
    indevice = 'Web Interface'
    filter = ('All' in filterInput) or (indevice in filterInput)
    if filter:
        mw = MidiOutWrapper(midiout, ch=ch)
        mw.send_program_change(pc)
        print(f'PC sent channel: {ch} value: {pc}')
        sio.emit('midi_sent', {'data': f'PC channel: {ch} value: {pc}'})
    else:
        send_ignore(indevice)

@sio.on('select_io')
def select_io(message):
    global filterInput
    setOutput(searchIO('output', message['data'][1]))
    temp = []
    temp.append(message['data'][0])
    setInputFilter(temp)
    sio.emit('outport', {'data': 'Connected', 'port': outport, 'outports':outports})
    sio.emit('io_set', {'data': {'input':message['data'][0], 'output':message['data'][1]}})
    send_settings()
    print(f"Input Filters changed to: {activeInput}")
    print(f"Output changed to: {activeOutput}")

@sio.on('rescan_io')
def rescan_io():
    scan_io('rescan')
    send_settings()

@sio.on('reload_keymap')
def reload_keymap():
    getMappedKeys()
    send_settings()

@sio.on('update_settings')
def update_settings():
    load_settings(settingsFile)
    send_settings()

@sio.on('apply_settings')
def apply_settings():
    print('apply_settings')
    # load_settings(settingsFile)
    # send_settings()


def send_ignore(indevice):
    sio.emit('client_msg', f"Message from {indevice} Ignored, outside of filter")

def send_client_msg(message):
    sio.emit('client_msg', message)

def send_settings():
    sio.emit('setup', {'outputs':filteredOutputList, 'inputs':filteredInputList, \
            'activeOutput':activeOutput, 'activeInput':activeInput,\
            'settings':settings, 'keymap':mappedkeys})


############### main functions #####################
def searchKeyMap(device, note, exact):
    print(f'searching keymap for note {note} on {device}')
    for key in mappedkeys:
        if exact:
            device = device
        else:
            device = key['device']
        if (str(key['note']) == str(note)) and (key['device'] == device):
            return key

def searchIO(type, device):
    global message_buffer, activeInput, activeOutput
    if type == 'input':
        print(f'Searching for Input Port number for {device}')
        if device == 'All':
            portnum = device
            activeInput=device
        else:
            if device in inports:
                portnum=inports.index(device)
                activeInput=device
            else:
                message_buffer.append(f"Input device {device} not found, setting input to All")
                print(f"Input device {device} not found, setting input to All")
                portnum = 'All'
                activeInput='All'
    elif type == 'output':
        print(f'Searching for Output Port number for {device}')
        if device in outports:
            portnum = outports.index(device)
            activeOutput = device
        else:
            message_buffer.append(f"Output device {device} not found, setting output to None")
            print(f"Output device {device} not found, setting output to None")
            portnum = 'None'
            activeOutput = 'None'
    return portnum

def loadKeyMap():
    mapfile = open(f'./keymaps/{keyMapFile}')
    map = json.loads(mapfile.read())
    mapfile.close()
    return map

def getMappedKeys():
    global mappedkeys
    tempKeys = loadKeyMap()
    mappedkeys = tempKeys
    return mappedkeys

def setOutput(port):
    global outport, activeOutput
    if port != 'None':
        midiout.close_port()
        midiout.open_port(port)
        outport = port
        activeOutput =outports[port]
    else:
        midiout.close_port()
        activeOutput = 'None'

def setInputFilter(new_inputs):
    global filterInput, activeInput
    filterInput = []
    for input in new_inputs:
        filterInput.append(input)
    activeInput = filterInput
    print(filterInput)

def load_settings(settings_file):
    global settings, defaultInput, defaultOutput, filterInput, ignoreInputs, ignoreOutputs, keyMapFile
    file = open(settings_file)
    settings = json.loads(file.read())
    keyMapFile = settings['keymap']
    defaultInput = settings['default_input']
    filterInput.append(defaultInput)
    defaultOutput = settings['default_output']
    ignoreInputs = settings['hide_inputs']
    ignoreOutputs = settings['hide_outputs']
    print(settings)
    file.close()

def save_settings(settings_file):
    file = open(settings_file)
    settings['last_input'] = filterInput
    settings['last_output'] = outport
    settings['last_keymap'] = keyMapFile
    print(settings)
    file.close()

def end_MIDI():
    for i in range (0, len(inports)):
        x = f'm{i}'
        globals()[x] = MidiInput(i, q)
    for i in range (0, len(inports)):
        x = f'm{i}'
        globals()[x].close_MidiInput()
        del globals()[x]
    midiout.close_port()
    gc.collect()
    print("MIDI Ports Closed")

def scan_io(type):
    global midiout, outport_name, inports, filteredOutputList, filteredInputList #, global_vars
    if type == 'rescan':
        end_MIDI()

    temp = []
    temp2 = []
    filteredInputList.clear()
    filteredOutputList.clear()
    outports.clear()
    inports = getAvailableIO(MidiIn)
    for i in inports:
        j = i.split(':')[0]
        temp2.append(j)
        if j not in ignoreInputs:
            temp.append(j)
    filteredInputList = temp
    inports = temp2

    # Dynamicly open midi inputs
    try:
        # print(inports)
        for i in range (0, len(inports)):
            x = f'm{i}'
            globals()[x] = MidiInput(i, q)

        midiout, outport_name = open_midioutput(outport)
        temp = midiout.get_ports()
        for o in temp:
            l = o.split(':')[0]
            outports.append(l)
            if l not in ignoreOutputs:
                filteredOutputList.append(l)
        print('MIDI Ports Opened')
    except (EOFError, KeyboardInterrupt):
        print("Exit.")


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



def midi_main(settings_file):
    global settingsFile
    settingsFile = settings_file
    load_settings(settingsFile)
    scan_io('initial')
    setOutput(searchIO('output', defaultOutput))
    searchIO('input', defaultInput)

    getMappedKeys()

    # connect to socketio server
    sio.connect(f'http://{server_addr}:{server_port}')

    # main program
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
                print(filterInput)
                filter = ('All' in filterInput) or (indevice in filterInput)
                if velocity > 0 and filter:
                    sio.emit('midi_msg', {'data': f'{msg}'})
                    if outport != 'None':
                        # print(settings['match_device'] == 'True')
                        remap = searchKeyMap(indevice, note, settings['match_device'] == 'True')
                        if remap:
                            if remap['type'] == 'PC':
                                mw = MidiOutWrapper(midiout, ch=remap['channel'])
                                mw.send_program_change(remap['value'])
                                print(f"PC sent channel: {remap['channel']} value: {remap['value']}")
                                sio.emit('midi_sent', {'data': f"Mapped to PC channel: {remap['channel']} value: {remap['value']}"})
                            elif remap['type'] == 'NOTE_ON':
                                mw = MidiOutWrapper(midiout, ch=remap['channel'])
                                mw.send_note_on(remap['new_note'])
                                print(f"sent NOTE_ON {remap['new_note']}")
                                sio.emit('midi_sent', {'data': f"Mapped to NOTE_ON Channel: {remap['channel']} Note: {remap['new_note']}"})
                            elif remap['type'] == 'OSC':
                                OSC_client = udp_client.SimpleUDPClient(remap['host'], remap['port'])
                                OSC_client.send_message(remap['message'],'')
                                print(f'OSC message {remap["message"]}')
                                sio.emit('midi_sent', {'data': f"Mapped to OSC message {remap['message']}"})
                        else:
                            mw = MidiOutWrapper(midiout, ch=channel)
                            mw.send_note_on(note)
                            print(f'sent {note}')
                            sio.emit('midi_sent', {'data': f'Channel: {channel} Note: {note}'})
                        time.sleep(0.1)
                elif (velocity > 0) and (not filter) and (not 'None' in filterInput):
                    print(filterInput)
                    send_ignore(indevice)
            time.sleep(0.01)
    except:
        print('Something Went Wrong')
        sio.emit('client_msg', 'Something Went Wrong with MIDI')
        save_settings(settings_file)
        end_MIDI()

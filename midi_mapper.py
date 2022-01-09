#!/usr/bin/env python3
#
# https://github.com/SpotlightKid/python-rtmidi
# https://python-osc.readthedocs.io
# midi_mapper.py
#

import sys
import time
import json
import queue
import socketio
import gc
import os
from pythonosc import udp_client

from rtmidi import MidiIn, MidiOut
from rtmidi.midiutil import open_midioutput, open_midiinput

### Local Modules
from modules.midioutwrapper import MidiOutWrapper
from modules.probe_ports import probe_ports, getAvailableIO
from modules.logger import *
from modules.keymap import getMappedKeys, searchKeyMap
from globals import owner, connectSocket, publishQueue, settingsCLASS, activeSettings

keyMapFile = 'default.json'
settingsFile = 'settings.json'
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
midi_mode = 'thru'
inports = getAvailableIO(MidiIn)
midiout, outport_name = open_midioutput(0)

q = queue.Queue()

sio = socketio.Client()
server_addr = 'localhost'
socket_port = '5005' # default, can be overridden in settings

########## Classes #############

# rtmidi
class MidiInput:
    def handle_midi_in(self, event, data):
        message, deltatime = event
        m = MidiMessage([self.device, message])
        q.put(m)
        # q.put([self.device, message])

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

#
class MidiMessage:
    def __init__(self, message, *type):
        self.indevice=message[0]
        # may need device maps to define channel numbers
        self.midi=message[1]
        self.channel=self.midi[0]-143
        self.note=self.midi[1]
        self.velocity=self.midi[2]
        if self.channel > 16 and self.channel < 100:
            if self.channel == 33 and self.note == 64 and self.velocity == 127:
                self.message_type = 'sustain_on'
            elif self.channel == 33 and self.note == 64 and self.velocity == 0:
                self.message_type = 'sustain_off'
            elif self.note == 7:
                self.message_type = 'volume'
            elif self.channel == 81:
                self.message_type = 'pitch_bend'
            elif self.channel == 33 and self.note == 1 and self.velocity > 0:
                self.message_type = 'modulation_on'
            elif self.channel == 33 and self.note == 1 and self.velocity == 0:
                self.message_type = 'modulation_off'
            else:
                self.message_type = 'control'
        elif self.channel < 0:
            self.channel = self.channel+16
            self.message_type = 'note_off'
        elif self.velocity == 0:
            self.message_type = 'note_off'
        else:
            self.message_type = 'note_on'
        if type:
            self.message_type = type[0]
        publishQueue.put(['MIDI',str(self.message_type)])

class webMidiNote(MidiMessage):
    def __init__(self, message):
        indevice = 'Web Interface'
        ch = int(message[0])+143
        note = int(message[1])
        vel = 127
        super().__init__([indevice, [ch, note, vel]])
    pass

class oscMidiNote(MidiMessage):
    def __init__(self, message):
        print(message)
        indevice = message[0]
        ch = message[1][0]+143
        note = message[1][1]
        message_type = message[2]
        if message_type == 'PROGRAM_CHANGE':
            super().__init__([indevice, [ch, note, 127]], 'program_change')
        elif message_type == 'NOTE_ON':
            super().__init__([indevice, [ch, note, 127]])

class webPCNote(MidiMessage):
    def __init__(self, message):
        indevice = 'Web Interface'
        ch = int(message[0])+143
        pc = int(message[1])
        super().__init__([indevice, [ch, pc, 127]], 'program_change')


################ socket IO #######################3

@sio.event
def connect():
    send_settings()
    for message in message_buffer:
        send_client_msg(message)
        print(message)
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
    wm = webMidiNote(message['data'])
    filter = ('All' in filterInput) or (indevice in filterInput)
    if filter:
        q.put(wm)
    else:
        send_ignore(indevice)

@sio.on('OSC2MIDI_in')
def OSC2MIDI_in(message):
    #build class for this
    indevice = message[0]
    ch = message[1][0]
    note = message[1][1]
    message_type = message[2]
    filter = ('All' in filterInput) or (indevice in filterInput)
    if filter:
        if message_type == 'NOTE_ON':
            # q.put([indevice, message[1]])
            q.put(MidiMessage([indevice, message[1]]))
            # sio.emit('midi_sent', {'data': f'NOTE_ON channel: {ch} value: {note}'})
        elif message_type == 'PROGRAM_CHANGE':
            message[1][0] = ch * 100 #setting a flag for MidiMessage
            # q.put([indevice, message[1]])
            q.put(MidiMessage([indevice, message[1]]))
            # sio.emit('midi_sent', {'data': f'PROGRAM_CHANGE channel: {ch} value: {note}'})
    else:
        send_ignore(indevice)

@sio.on('webPCIn')
def webPCIn(message):
    #build class for this
    ch = int(message['data'][0])
    pc = int(message['data'][1])
    indevice = 'Web Interface'
    wpc = webPCNote(message['data'])
    filter = ('All' in filterInput) or (indevice in filterInput)
    if filter:
        print(wpc.message_type)
        q.put(wpc)
        # mw = MidiOutWrapper(midiout, ch=ch)
        # mw.send_program_change(pc)
        # print(f'PC sent channel: {ch} value: {pc}')
        # sio.emit('midi_sent', {'data': f'PC channel: {ch} value: {pc}'})
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
    logs.info(f"Input Filters changed to: {activeInput}")
    logs.info(f"Output changed to: {activeOutput}")

@sio.on('rescan_io')
def rescan_io():
    # temp workaround for rescan not working
    sio.emit('restart_midi')
    # scan_io('rescan')
    # send_settings()

@sio.on('reload_keymap')
def reload_keymap():
    global mappedkeys
    mappedkeys = getMappedKeys(keyMapFile)
    send_settings()

@sio.on('open_keymap')
def open_keymap(openMapFile):
    global mappedkeys, settings, keyMapFile
    settings['last_keymap'] = keyMapFile
    mappedkeys = getMappedKeys(openMapFile)
    settings['keymap'] = openMapFile
    save_midiSetting(settingsFile, settings)
    keyMapFile = openMapFile
    activeSettings.setValue('keyMapFile',keyMapFile)
    send_settings()

@sio.on('set_mode')
def set_mode(message):
    global midi_mode
    midi_mode = message
    print(f"MIDI Mode changed to: {midi_mode}")
    logs.info(f"MIDI Mode changed to: {midi_mode}")
    send_client_msg(f"MIDI Mode changed to: {midi_mode}")
    if midi_mode == 'Mapped' and not map:
        send_client_msg(f"No Keymap Loaded")
        set_mode('Thru')
    activeSettings.setValue('midi_mode', midi_mode)
    send_settings()
    # might still need dummy note
    q.put(MidiMessage(['dummy message', [0,0,0]]))

@sio.on('exact_match')
def exact_match(message):
    global match_device
    match_device = message
    activeSettings.setValue('match_device', message)
    send_settings()
    print(f"Match device changed to: {match_device}")

@sio.on('update_settings')
def update_settings():
    load_settings(settingsFile)
    send_settings()

@sio.on('quit')
def quit():
    save_midiSetting(settingsFile, settings)

@sio.on('save_settings')
def save_settings(settings):
    save_midiSetting(settingsFile, settings)
    send_client_msg('MIDI Settings Saved')

@sio.on('apply_settings')
def apply_settings():
    # temp workaround for rescan not working
    sio.emit('restart_midi')

@sio.on('restart_midi')
def restart_midi():
    # sio.disconnect()
    print('MIDI Restarted')


##################### Functions


def send_ignore(indevice):
    sio.emit('client_msg', f"Message from {indevice} Ignored, outside of filter")

def send_client_msg(message):
    sio.emit('client_msg', message)

def send_settings():
    activeSettings.read()
    sio.emit('setup', {'match_device':match_device, 'midi_mode':midi_mode, 'outputs':filteredOutputList, 'inputs':filteredInputList, \
            'activeOutput':activeOutput, 'activeInput':activeInput,\
            'settings':settingsCLASS.config, 'keymap':mappedkeys, 'keyMapFile':keyMapFile, 'activeSettings':vars(activeSettings)})

def searchIO(type, device):
    global message_buffer, activeInput, activeOutput
    if type == 'input':
        print(f'Searching for Inputs for {device}')
        if device == 'All' or 'Web Interface' or 'OSC2MIDI':
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
        print(f'Searching for Outputs for {device}')
        if device in outports:
            portnum = outports.index(device)
            activeOutput = device
        else:
            message_buffer.append(f"Output device {device} not found, setting output to None")
            print(f"Output device {device} not found, setting output to None")
            portnum = 'None'
            activeOutput = 'None'
    activeSettings.setValue('activeInput',activeInput)
    activeSettings.setValue('activeOutput',activeOutput)
    return portnum

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
    activeSettings.setValue('activeOutput',activeOutput)

def setInputFilter(new_inputs):
    global filterInput, activeInput
    filterInput = []
    for input in new_inputs:
        filterInput.append(input)
    activeInput = filterInput
    activeSettings.setValue('activeInput',activeInput)

def load_settings(settings_file):
    global settings, defaultInput, defaultOutput, filterInput, ignoreInputs, \
            ignoreOutputs, keyMapFile, socket_port, midi_mode, match_device

    settingsCLASS.load_config()
    settings = settingsCLASS.config
    keyMapFile = settingsCLASS.keymap
    defaultInput = settingsCLASS.default_input
    defaultOutput = settingsCLASS.default_output
    ignoreInputs = settingsCLASS.hide_inputs
    ignoreOutputs = settingsCLASS.hide_outputs
    socket_port = settingsCLASS.socket_port
    midi_mode = settingsCLASS.midi_mode
    match_device = settingsCLASS.match_device
    activeSettings.setValue('keyMapFile', keyMapFile)
    activeSettings.setValue('midi_mode', midi_mode)
    activeSettings.setValue('match_device', match_device)
    filterInput.clear()
    filterInput.append(defaultInput)

def save_midiSetting(settings_file, new_settings):

    settingsCLASS.config = new_settings
    settingsCLASS.read_config()
    settingsCLASS.last_input = filterInput
    settingsCLASS.last_output = activeOutput
    settingsCLASS.last_keymap = keyMapFile
    settingsCLASS.write_config()
    print('MIDI Settings Saved')

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
    global midiout, outport_name, inports, filteredOutputList, filteredInputList, activeOutput, activeInput
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

        midiout, outport_name = open_midioutput(0)

        temp = midiout.get_ports()

        for o in temp:
            l = o.split(':')[0]
            outports.append(l)
            if l not in ignoreOutputs:
                filteredOutputList.append(l)

        print('MIDI Ports Opened')

        # select default i\o if available
        if defaultOutput in outports:
            setOutput(searchIO('output', defaultOutput))
        if activeOutput not in outports:
            activeOutput = 'None'
        searchIO('input', defaultInput)

    except Exception as err:
        print('Something Went Wrong')
        logs.error(f'Something Went Wrong While Scanning I/O: {err}')
        sio.emit('client_msg', f'Something Went Wrong with MIDI: {err}')
        sio.emit('restart_midi')
        # end_MIDI()
        print("Exit.")


############### Main

def midi_main():
    logs.debug(f'midi_mapper.py running as PID: {os.getpid()} as User: {owner(os.getpid())}')
    global settingsFile, midi_mode, mappedkeys
    logs.info(f"{ __name__} started")
    settingsFile = ''
    settings_file = ''
    load_settings(settingsFile)
    mappedkeys = getMappedKeys(keyMapFile)
    scan_io('initial')
    setOutput(searchIO('output', defaultOutput))
    searchIO('input', defaultInput)

    connectSocket(sio, server_addr, socket_port)

    # main program
    print("Entering MIDI loop. ")


    try:
        try:
            while True:
                timer = time.time()
                while midi_mode == 'Mapped':
                    # msg = MidiMessage(q.get(1))
                    msg = q.get(1)
                    if msg:
                        filter = ('All' in filterInput) or (msg.indevice in filterInput)
                        if msg.velocity > 0 and filter and msg.message_type == 'note_on' and msg.channel > 0:
                            sio.emit('midi_msg', {'data': {'device':msg.indevice, 'midi':msg.midi, 'message_type':msg.message_type}})
                            remap = searchKeyMap(mappedkeys, msg.indevice, msg.note, settings['match_device'] == 'True')

                            if remap and remap['type']=="OSC":
                                try:
                                    OSC_client = udp_client.SimpleUDPClient(remap['host'], remap['port'])
                                    OSC_client.send_message(remap['message'],'')
                                    print(f'OSC message {remap["message"]}')
                                    sio.emit('midi_sent', {'data': f"Mapped to OSC message {remap['message']}"})
                                except Exception as err:
                                    sio.emit('client_msg', f"Error: {remap['host']}:{remap['port']} {err}")

                            if remap and remap['type']=="MQTT":
                                try:
                                    publishQueue.put([remap['topic'], remap['message']])
                                    print(f"MQTT topic {remap['topic']} message {remap['message']}")
                                    sio.emit('midi_sent', {'data': f"Mapped to MQTT topic {remap['topic']} message {remap['message']}"})
                                except Exception as err:
                                    sio.emit('client_msg', f"Error publishing {err}")

                            if activeOutput != 'None':
                                # print(settings['match_device'] == 'True')
                                if remap:
                                    print(f"Mapping for note {msg.note} on {msg.indevice} found")
                                    if remap['type'] == 'PROGRAM_CHANGE':
                                        mw = MidiOutWrapper(midiout, ch=remap['channel'])
                                        mw.send_program_change(remap['value'])
                                        print(f"PC sent channel: {remap['channel']} value: {remap['value']}")
                                        sio.emit('midi_sent', {'data': f"Mapped to PC channel: {remap['channel']} value: {remap['value']}"})
                                    elif remap['type'] == 'NOTE_ON':
                                        mw = MidiOutWrapper(midiout, ch=remap['channel'])
                                        mw.send_note_on(remap['new_note'])
                                        # mw.send_note_off(remap['new_note'])
                                        print(f"sent NOTE_ON {remap['new_note']}")
                                        sio.emit('midi_sent', {'data': f"Mapped to NOTE_ON Channel: {remap['channel']} Note: {remap['new_note']}"})
                                else:
                                    mw = MidiOutWrapper(midiout, ch=msg.channel)
                                    mw.send_note_on(msg.note)
                                    print(f"No mapping for note {msg.note} on {msg.indevice} found")
                                    print(f"Sent {msg.note}")
                                    sio.emit('midi_sent', {'data': f"Channel: {msg.channel} Note: {msg.note}"})
                                time.sleep(0.1)
                        elif (msg.velocity > 0) and (not filter) and (not 'None' in filterInput):
                            print(filterInput)
                            send_ignore(msg.indevice)
                time.sleep(0.01)

                while midi_mode == 'Thru':
                    # msg = MidiMessage(q.get(1))
                    msg = q.get(1)
                    filter = ('All' in filterInput) or (msg.indevice in filterInput)
                    if filter and msg.channel > 0:
                        sio.emit('midi_msg', {'data': {'device':msg.indevice, 'midi':msg.midi}})
                        # sio.emit('midi_msg', {'data': f'{msg.indevice} : {msg.midi}'})
                        if msg.message_type == 'note_on':
                            mw = MidiOutWrapper(midiout, ch=msg.channel)
                            mw.send_note_on(msg.note, msg.velocity)
                            print(f"Sent {msg.note} on Channel: {msg.channel}")
                            sio.emit('midi_sent', {'data': f"{msg.message_type} Channel: {msg.channel} Note: {msg.note}"})
                        elif msg.message_type == 'note_off':
                            mw.send_note_off(msg.note)
                            sio.emit('midi_sent', {'data': f"{msg.message_type} Channel: {msg.channel} Note: {msg.note}"})
                        elif msg.message_type == 'sustain':
                            mw = MidiOutWrapper(midiout, ch=msg.channel)
                            mw.send_control_change(64, msg.velocity, ch=msg.channel)
                            print(f"Sent sustain on Channel: {msg.channel}")
                            sio.emit('midi_sent', {'data': f"Sent sustain on Channel: {msg.channel}"})
                        elif msg.message_type == 'program_change':
                            mw = MidiOutWrapper(midiout, ch=msg.channel)
                            mw.send_program_change(msg.note)
                            print(f"PC sent channel: {msg.channel} value: {msg.note}")
                            sio.emit('midi_sent', {'data': f"Mapped to PC channel: {msg.channel} value: {msg.note}"})
                        else:
                            print(msg.message_type)

        except Exception as err:
            print(f"{ __name__} - Something Went Wrong with MIDI {err}")
            logs.error(f"{ __name__} - Something Went Wrong with MIDI {err}")
            sio.emit('client_msg', f'Something Went Wrong with MIDI - {err} - Restarting MIDI' )
            sio.emit('restart_midi')
    except Exception as err:
        save_midiSetting(settings_file, settings)
        end_MIDI()
        logs.info(f"{ __name__} - MIDI Ended - {err} ")
        print('Exiting')

if __name__ == '__main__':
    midi_main()

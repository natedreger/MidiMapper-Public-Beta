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
from globals import *

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

class MidiDevice:
    filename = 'knowndevices.dat'
    knowndevices = []
    deviceConfigs = []
    def __init__(self):
        self.device_name = 'default'
        self.ch_offset = 143
        self.note_on = []
        self.note_off = []
        self.sustain_on = []
        self.sustain_off = []
        self.pitchUp= []
        self.pitchDown= []
        self.mod_on= []
        self.mod_off=[]
        self.volume = []

    def load(self):
        with open(MidiDevice.filename, 'r') as config_file:
            MidiDevice.deviceConfigs = json.load(config_file)
            for key in MidiDevice.deviceConfigs:
                MidiDevice.knowndevices.append(key['device_name'])

    def save(self):
    	with open(MidiDevice.filename, 'w') as config_file:
            json.dump(MidiDevice.deviceConfigs, config_file, indent=4)

    def search(self, device_name):
        try: return MidiDevice.deviceConfigs[MidiDevice.knowndevices.index(device_name)]
        except ValueError: return MidiDevice.deviceConfigs[MidiDevice.knowndevices.index('default')]
    # return # return result

    def setAttached(self):
    	pass

    def addDeviceConfig(self):
        config = vars(self)
        MidiDevice.deviceConfigs.append(config)
        self.save()

    def getMessageType(self, device, midi):
        deviceMap = self.search(device)
        message_type = f''
        for key in deviceMap:
            if midi == deviceMap[key]:
                message_type = key
            else:
                # some kinda nested if loop
                pass
        # find midi pattern in devicemap
        # return key
        return message_type

devices = MidiDevice()
devices.load()

class MidiMessage:
    def __init__(self, message, *type):
        # led1.blue()
        self.indevice=message[0]
        # may need device maps to define channel numbers
        if self.indevice in MidiDevice.knowndevices:
            config = MidiDevice.deviceConfigs[MidiDevice.knowndevices.index(self.indevice)]
        else:
            config = MidiDevice.deviceConfigs[MidiDevice.knowndevices.index('default')]
        self.midi=message[1]
        self.channel=self.midi[0] - config['ch_offset']
        self.note=self.midi[1]
        self.velocity=self.midi[2]
        print(MidiDevice.getMessageType(devices, self.indevice, self.midi))
        if self.channel > 16:
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
        indevice = 'OSC2MIDI'
        message_type = message[0]
        ch = int(message[1])+143
        note = int(message[2])
        try: vel = int(message[3])
        except: vel = 1
        super().__init__([indevice, [ch, note, vel]], message_type)


class webPCNote(MidiMessage):
    def __init__(self, message):
        indevice = 'Web Interface'
        ch = int(message[0])+143
        pc = int(message[1])
        super().__init__([indevice, [ch, pc, 127]], 'program_change')


################ socket IO #######################3
# class socketioMessage_Class():
#     def __init__(self):
#         self.handle = ''
#         self.data = ''
#         pass
#     def send(self, handle, data):
#         self.handle = handle
#         self.data = data
#         socketioMessageQueue.put(vars(self))
#
# socketioMessage = socketioMessage_Class()

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
    oscMid = oscMidiNote(message)
    filter = ('All' in filterInput) or (indevice in filterInput)
    if filter:
        q.put(oscMid)
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
        q.put(wpc)
    else:
        send_ignore(indevice)

@sio.on('select_io')
def select_io(message):
    global filterInput
    setOutput(searchIO('output', message['data'][1]))
    temp = []
    temp.append(message['data'][0])
    setInputFilter(temp)
    socketioMessage.send('outport', {'data': 'Connected', 'port': outport, 'outports':outports})
    socketioMessage.send('io_set', {'data': {'input':message['data'][0], 'output':message['data'][1]}})
    send_settings()
    print(f"Input Filters changed to: {activeInput}")
    print(f"Output changed to: {activeOutput}")
    logs.info(f"Input Filters changed to: {activeInput}")
    logs.info(f"Output changed to: {activeOutput}")

@sio.on('rescan_io')
def rescan_io():
    # temp workaround for rescan not working
    socketioMessage.send('restart_midi',True)
    # scan_io('rescan')
    # send_settings()

@sio.on('reload_keymap')
def reload_keymap():
    global mappedkeys
    mappedkeys = getMappedKeys(keyMapFile)
    socketioMessage.send('refresh_keymap', mappedkeys)
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
    socketioMessage.send('refresh_keymap', mappedkeys)
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
    q.put(MidiMessage(['dummy message', [0,0,0]]))

@sio.on('exact_match')
def exact_match(message):
    global match_device
    match_device = message
    print(message)
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
    socketioMessage.send('restart_midi',True)

@sio.on('restart_midi')
def restart_midi(data):
    # sio.disconnect()
    print('MIDI Restarted')


##################### Functions

def learnMidiDevice():
    # set flag to escape
    try:
        print('///////////////////////////////////////')
        print('Use ctrl-c to exit to main')
        print('Set Controller to Channel 1 then')
        print('Press Any Key on controller to Start')
        device = q.get(1)
        # see if device exists, prompt to exit
        if device.indevice in MidiDevice.knowndevices:
            again = str(input(f'{device.indevice} already learned, learn again? y/n > '))
            if again == 'n':
                print ('\n use ctrl-c to exit \n')
                time.sleep(5)
            elif again == 'y':
                print('\n OK \n')
                pass
        setattr(newDevice, 'device_name', device.indevice)
        setattr(newDevice, 'ch_offset', device.midi[0] - 1)
        q.get(1) # toss the key up
        print(f'Ready to learn keys on {device.indevice}')

        print('Press and Hold any Note Key')
        setattr(newDevice, 'note_on', q.get(1).midi)
        print(f'Captured note_on, release key')
        setattr(newDevice, 'note_off', q.get(1).midi)
        print(f'Captured note_off')

        print('Press and Hold Sustain')
        setattr(newDevice, 'sustain_on', q.get(1).midi)
        print(f'Captured sustain_on, release sustain')
        setattr(newDevice, 'sustain_off', q.get(1).midi)
        print(f'Captured sustain_off')

        print('Press and Hold Pitch Up')
        on = []
        time.sleep(2)
        while True:
            try: on.append(q.get(0).midi)
            except: break
        try:
            setattr(newDevice, 'pitchUp', on[len(on)-1])
            print(f'Captured pitchup')
        except IndexError:
            print('Failed to capture pitch up')
        q.queue.clear()

        print('Press and Hold Pitch Down')
        on = []
        time.sleep(2)
        while True:
            try: on.append(q.get(0).midi)
            except: break
        try:
            setattr(newDevice, 'pitchDown', on[len(on)-1])
            print(f'Captured pitchDown')
        except IndexError:
            print('Failed to capture pitch down')

        print('Press and Hold Mod')
        on = []
        time.sleep(2)
        while True:
            try: on.append(q.get(0).midi)
            except: break
        try:
            setattr(newDevice, 'mod', on[len(on)-1])
            print(f'Captured mod_on, release mod')
        except IndexError:
            print('failed to capture mod')

        print('Adjust Volume')
        on = []
        time.sleep(2)
        while True:
            try: on.append(q.get(0).midi)
            except: break
        try:
            setattr(newDevice, 'volumeUp', on[len(on)-1])
            print(f'Captured volume')
        except IndexError:
            print('failed to volume')

        newDevice.addDeviceConfig()
        print('All done!')
        print(vars(newDevice))
    except KeyboardInterrupt:
        print('\nExiting Learn Device without saving\n')
        pass

def send_ignore(indevice):
    socketioMessage.send('client_msg', f"Message from {indevice} Ignored, outside of filter")

def send_client_msg(message):
    socketioMessage.send('client_msg', message)

def send_settings():
    activeSettings.read()
    settingsCLASS.load_config()
    socketioMessage.send('settings', {'match_device':activeSettings.match_device,'midi_mode':activeSettings.midi_mode, 'availableInputs':activeSettings.availableInputs, 'availableOutputs':activeSettings.availableOutputs, \
                    'activeInput':activeSettings.activeInput, 'activeOutput':activeSettings.activeOutput, 'settings':settingsCLASS.config, 'keyMapFile':activeSettings.keyMapFile})

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
        setattr(activeSettings, 'availableOutputs', filteredOutputList)
        setattr(activeSettings, 'availableInputs', filteredInputList)


    except Exception as err:
        print('Something Went Wrong')
        logs.error(f'Something Went Wrong While Scanning I/O: {err}')
        socketioMessage.send('client_msg', f'Something Went Wrong with MIDI: {err}')
        socketioMessage.send('restart_midi',True)
        print("Exit.")

def bypassMode(msg):
    if msg.message_type != 'note_off':
        socketioMessage.send('midi_msg', {'data': {'device':msg.indevice, 'midi':msg.midi, 'message_type':msg.message_type}})

def mapMode(msg):
    print(msg.indevice, msg.message_type)
    # publishQueue.put(['MIDI',f'Received {msg.indevice} {msg.midi}'])
    filter = ('All' in filterInput) or (msg.indevice in filterInput)
    if msg.velocity > 0 and filter and msg.message_type == 'note_on' and msg.channel > 0:
        ledQueue.put('led1.blue()')
        socketioMessage.send('midi_msg', {'data': {'device':msg.indevice, 'midi':msg.midi, 'message_type':msg.message_type}})
        remap = searchKeyMap(mappedkeys, msg.indevice, msg.note, activeSettings.match_device)

        if remap:
            if remap['type'] == "OSC":
                try:
                    OSC_client = udp_client.SimpleUDPClient(remap['host'], remap['port'])
                    OSC_client.send_message(remap['message'],'')
                    print(f'OSC message {remap["message"]}')
                    socketioMessage.send('midi_sent', {'data': f"Mapped to OSC message {remap['message']}"})
                    ledQueue.put('led1.orange()')
                except Exception as err:
                    socketioMessage.send('client_msg', f"Error: {remap['host']}:{remap['port']} {err}")

            if remap['type'] == "MQTT":
                try:
                    publishQueue.put([remap['topic'], remap['message']])
                    print(f"MQTT topic {remap['topic']} message {remap['message']}")
                    socketioMessage.send('midi_sent', {'data': f"Mapped to MQTT topic {remap['topic']} message {remap['message']}"})
                    ledQueue.put('led1.orange()')
                except Exception as err:
                    socketioMessage.send('client_msg', f"Error publishing {err}")

            if activeOutput != 'None':
                if remap:
                    print(f"Mapping for note {msg.note} on {msg.indevice} found")
                    if remap['type'] == 'PROGRAM_CHANGE':
                        mw = MidiOutWrapper(midiout, ch=remap['channel'])
                        mw.send_program_change(remap['value'])
                        print(f"PC sent channel: {remap['channel']} value: {remap['value']}")
                        socketioMessage.send('midi_sent', {'data': f"Mapped to PC channel: {remap['channel']} value: {remap['value']}"})
                        ledQueue.put('led1.orange()')
                    elif remap['type'] == 'NOTE_ON':
                        mw = MidiOutWrapper(midiout, ch=remap['channel'])
                        mw.send_note_on(remap['new_note'])
                        # mw.send_note_off(remap['new_note'])
                        print(f"sent NOTE_ON {remap['new_note']}")
                        socketioMessage.send('midi_sent', {'data': f"Mapped to NOTE_ON Channel: {remap['channel']} Note: {remap['new_note']}"})
                        ledQueue.put('led1.orange()')
                else:
                    mw = MidiOutWrapper(midiout, ch=msg.channel)
                    mw.send_note_on(msg.note)
                    print(f"No mapping for note {msg.note} on {msg.indevice} found")
                    print(f"Sent {msg.note}")
                    socketioMessage.send('midi_sent', {'data': f"Channel: {msg.channel} Note: {msg.note}"})
                    ledQueue.put('led1.orange()')
                time.sleep(0.1)
            if remap['echo'] == True:
                mw = MidiOutWrapper(midiout, ch=msg.channel)
                mw.send_note_on(msg.note, msg.velocity)

        else:
            # this is in the wrong spot??? note is sending with midi out set to none
            # if note is not remapped, pass Through
            mw = MidiOutWrapper(midiout, ch=msg.channel)
            mw.send_note_on(msg.note, msg.velocity)
            print(f"No mapping for note {msg.note} on {msg.indevice} found")
            print(f"Sent {msg.note}")
            socketioMessage.send('midi_sent', {'data': f"Channel: {msg.channel} Note: {msg.note}"})
            ledQueue.put('led1.orange()')

    elif msg.message_type == 'program_change':
        ledQueue.put('!!!!!!!!!! PC IN MAPPED BLUE !!!!')
        mw = MidiOutWrapper(midiout, ch=msg.channel)
        mw.send_program_change(msg.note)
        print(f"PC sent channel: {msg.channel} value: {msg.note}")
        socketioMessage.send('midi_sent', {'data': f"Mapped to PC channel: {msg.channel} value: {msg.note}"})
        ledQueue.put('led1.orange()')
    elif (msg.velocity > 0) and (not filter) and (not 'None' in filterInput):
        send_ignore(msg.indevice)
    ledQueue.put('led1.green()')
    # ledQueue.put('!!!!!!!!!! END MAPPED GREEEN !!!!')
    print('waiting for MIDI input')



def thruMode(msg):
    # publishQueue.put(['MIDI',f'Received {msg.indevice} {msg.midi}'])
    filter = ('All' in filterInput) or (msg.indevice in filterInput)
    if filter and msg.channel > 0:
        ledQueue.put('led1.blue()')
        mw = MidiOutWrapper(midiout, ch=msg.channel)
        socketioMessage.send('midi_msg', {'data': {'device':msg.indevice, 'midi':msg.midi, 'message_type':msg.message_type}})
        if msg.message_type == 'note_on':
            # mw = MidiOutWrapper(midiout, ch=msg.channel)
            mw.send_note_on(msg.note, msg.velocity)
            print(f"Sent {msg.note} on Channel: {msg.channel}")
            socketioMessage.send('midi_sent', {'data': f"{msg.message_type} Channel: {msg.channel} Note: {msg.note}"})
            ledQueue.put('led1.orange()')
        elif msg.message_type == 'note_off':
            mw.send_note_off(msg.note)
            socketioMessage.send('midi_sent', {'data': f"{msg.message_type} Channel: {msg.channel} Note: {msg.note}"})
            ledQueue.put('led1.orange()')
        elif msg.message_type == 'sustain':
            # mw = MidiOutWrapper(midiout, ch=msg.channel)
            mw.send_control_change(64, msg.velocity, ch=msg.channel)
            print(f"Sent sustain on Channel: {msg.channel}")
            socketioMessage.send('midi_sent', {'data': f"Sent sustain on Channel: {msg.channel}"})
            ledQueue.put('led1.orange()')
        elif msg.message_type == 'program_change':
            # mw = MidiOutWrapper(midiout, ch=msg.channel)
            mw.send_program_change(msg.note)
            print(f"PC sent channel: {msg.channel} value: {msg.note}")
            socketioMessage.send('midi_sent', {'data': f"Mapped to PC channel: {msg.channel} value: {msg.note}"})
            ledQueue.put('led1.orange()')
        else:
            print(msg.message_type)
    ledQueue.put('led1.green()')
    print('waiting for MIDI input')

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
    send_settings()

    if __name__ != '__main__':
        connectSocket(sio, server_addr, socket_port)

    elif __name__ == '__main__':
        print('\n')
        learn = str(input('Learn MIDI Device? y/n > '))
        if learn == 'y':
            learnMidiDevice()
            pass
        else:
            print('\n')
            pass

    # main program
    print("Entering MIDI loop. ")
    print('waiting for MIDI input')
    ledQueue.put('led1.green()')
    try:
        try:
            while True:
                timer = time.time()
                while midi_mode == 'Mapped':
                    msg = q.get(1)
                    mapMode(msg)
                while midi_mode == 'Thru':
                    msg = q.get(1)
                    print(msg)
                    thruMode(msg)
                while midi_mode == 'Bypass':
                    msg = q.get(1)
                    bypassMode(msg)
        except Exception as err:
            print(f"{ __name__} - Something Went Wrong with MIDI {err}")
            logs.error(f"{ __name__} - Something Went Wrong with MIDI {err}")
            socketioMessage.send('client_msg', f'Something Went Wrong with MIDI - {err} - Restarting MIDI' )
            ledQueue.put("led1.blinkFast('red')")
            socketioMessage.send('restart_midi',True)
    except Exception as err:
        save_midiSetting(settings_file, settings)
        end_MIDI()
        logs.info(f"{ __name__} - MIDI Ended - {err} ")
        print('Exiting')

    except KeyboardInterrupt:
        if __name__ == '__main__':
            print('\nquit\n')
            os._exit(os.EX_OK)
        else:
            pass

if __name__ == '__main__':
    midi_main()

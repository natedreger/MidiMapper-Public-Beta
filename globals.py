import pwd
import sys
import os
import json
from dotenv import load_dotenv
from multiprocessing import Queue

####### GLOBAL CONSTANTS ############
sys.path.insert(0, os.path.dirname(__file__))
load_dotenv('.env')
SETTINGS_FILE=os.environ.get('SETTINGS_FILE')
VERSION=os.environ.get('VERSION')

publishQueue = Queue()

############## GLOBAL FUNCTIONS ###############

UID   = 1
EUID  = 2


def owner(pid):
    '''Return username of UID of process pid'''
    for ln in open('/proc/%d/status' % pid):
        if ln.startswith('Uid:'):
            uid = int(ln.split()[UID])
            return pwd.getpwuid(uid).pw_name

def connectSocket(socketName, socket_addr, socket_port):
    connected = False
    while not connected:
        try:
            socketName.connect(f'http://{socket_addr}:{socket_port}')
        except Exception as err:
            print("ConnectionError: %s", err)
            logs.error(f"{ __name__} - {err}")
        else:
            print("Connected!")
            connected = True

def load_settings(settings_file):
    global settings, defaultInput, defaultOutput, filterInput, ignoreInputs, \
            ignoreOutputs, keyMapFile, socket_port, midi_mode, match_device
    file = open(settings_file)
    settings = json.loads(file.read())
    file.close()

    keyMapFile = settings['keymap']
    defaultInput = settings['default_input']
    defaultOutput = settings['default_output']
    ignoreInputs = settings['hide_inputs']
    ignoreOutputs = settings['hide_outputs']
    socket_port = settings['socket_port']
    midi_mode = settings['midi_mode']
    match_device = settings['match_device']
    filterInput.clear()
    filterInput.append(defaultInput)

def read_settings(settings_file):
    file = open(settings_file)
    settings = json.loads(file.read())
    file.close()
    return settings

def save_settings(settings_file, new_settings):
    settings = new_settings
    settings['last_input'] = filterInput
    settings['last_output'] = activeOutput
    settings['last_keymap'] = keyMapFile

    file = open(settings_file,'w')
    file.write(json.dumps(settings))
    file.close()
    print('MIDI Settings Saved')

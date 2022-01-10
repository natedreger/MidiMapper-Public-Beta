import pwd
import sys
import os
import json
import getpass
import platform
from dotenv import load_dotenv
from multiprocessing import Queue
from cryptography.fernet import Fernet

###### Local Modules #####


####### GLOBAL CONSTANTS ############
sys.path.insert(0, os.path.dirname(__file__))
load_dotenv('.env')
SETTINGS_FILE=os.environ.get('SETTINGS_FILE')
VERSION=os.environ.get('VERSION')

osName = platform.system()
appDir = os.getcwd()
path = appDir.split("/")
user = getpass.getuser()

publishQueue = Queue()
socketioMessageQueue = Queue()

if osName == 'Linux':
    path2config = appDir
    path2key = f'/home/{user}/.ssh/midiMapper.key'

############## GLOBAL FUNCTIONS ###############

#####  Crypto \\\\\\\\\\\\\\
def genwrite_key():
    key = Fernet.generate_key()
    with open (path2key, 'wb') as key_file:
        key_file.write(key)

def call_key():
    try:
        return open(path2key, 'rb').read()
    except FileNotFoundError as err:
        genwrite_key()

def encrypt(data):
    # get the key and generate if not found
    key = call_key()
    while not key:
        genwrite_key()
        key = call_key()
    a = Fernet(key)
    encryptedData = a.encrypt(data.encode())
    return encryptedData

def decrypt(data):
    key = call_key()
    a = Fernet(key)
    decryptedData = a.decrypt(data)
    return decryptedData.decode('utf-8')

def checkPaswd(password):
    # assume any password under 50 characters is in plaintext and encrypt
    if len(password) in range(1,51):
        new = encrypt(password)
        return [False, new]
    else: return [True]

#####////////////////////////////

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

############## Classes ##########################

class SettingsManager:
    def __init__(self, file):
        self.filename = file
        self.config = {}

        try:
            with open(self.filename) as config:
                self.config = json.load(config)
                print('SettingsManager: SettingsManager Init')
        except:
            print("SettingsManager: Cannot open config file")

    def write_config(self):

        self.config['midi_mode'] = self.midi_mode
        self.config['default_output'] = self.default_output
        self.config['default_input'] = self.default_input
        self.config['last_input'] = self.last_input
        self.config['match_device'] = self.match_device
        self.config['last_output'] = self.last_output
        self.config['keymap'] = self.keymap
        self.config['last_keymap'] = self.last_keymap
        self.config['hide_inputs'] = self.hide_inputs
        self.config['hide_outputs'] = self.hide_outputs
        self.config['socket_port'] = self.socket_port
        self.config['osc_port'] = self.osc_port
        self.config['mqtt_broker'] = self.mqtt_broker
        self.config['mqtt_port'] = self.mqtt_port
        self.config['mqtt_user'] = self.mqtt_user
        # self.config['mqtt_paswd'] = self.mqtt_paswd
        encryptedPwd = checkPaswd(self.mqtt_paswd)
        # if the password was not encrpyted get the encypted one and store it
        if not encryptedPwd[0]:
            self.mqtt_paswd = encryptedPwd[1].decode('utf-8')
        self.config['mqtt_paswd'] = self.mqtt_paswd

        with open(self.filename, 'w') as config_file:
            json.dump(self.config, config_file)
        with open(self.filename, 'r') as config_file:
            self.config = json.load(config_file)
        print("SettingsManager: Settings Saved Successfully")

    def read_config(self):
        print("SettingsManager: Loading Config")
        self.midi_mode = self.config['midi_mode']
        self.default_output = self.config['default_output']
        self.default_input = self.config['default_input']
        self.last_input = self.config['last_input']
        self.match_device = self.config['match_device']
        self.last_output = self.config['last_output']
        self.keymap = self.config['keymap']
        self.last_keymap = self.config['last_keymap']
        self.hide_inputs = self.config['hide_inputs']
        self.hide_outputs = self.config['hide_outputs']
        self.socket_port = self.config['socket_port']
        self.osc_port = self.config['osc_port']
        self.mqtt_broker = self.config['mqtt_broker']
        self.mqtt_port = self.config['mqtt_port']
        self.mqtt_user = self.config['mqtt_user']
        # self.mqtt_paswd = self.config['mqtt_paswd']
        encryptedPwd = checkPaswd(self.config['mqtt_paswd'])
        # if the password was not encrpyted get the encypted one and store it
        if not encryptedPwd[0]:
            self.mqtt_paswd = encryptedPwd[1].decode('utf-8')
            self.write_config()
        else:
            self.mqtt_paswd = self.config['mqtt_paswd']
        print("SettingsManager: Settings Loaded Successfully")

    def load_config(self):
        print("SettingsManager: Reloading Config")
        with open(self.filename, 'r') as config_file:
            self.config = json.load(config_file)
        self.read_config()

settingsCLASS = SettingsManager(SETTINGS_FILE)
settingsCLASS.read_config()


class ActiveSettings_Class:
    def __init__(self):
        self.tempFile = 'activeSettings.tmp'
        with open(self.tempFile, 'w') as file:
            json.dump(vars(self), file)

    def write(self):
        with open(self.tempFile, 'w') as file:
            json.dump(vars(self), file)

    def read(self):
        with open(self.tempFile, 'r') as file:
            active = json.load(file)
            for key in active:
                setattr(self, key, active[key])

    def setValue(self, key, value):
        setattr(self, key, value)
        self.write()
        self.read()

activeSettings = ActiveSettings_Class()
activeSettings.read()

# print(test.match_device)

# activeSettings = {}

# def load_settings(settings_file):
#     global settings, defaultInput, defaultOutput, filterInput, ignoreInputs, \
#             ignoreOutputs, keyMapFile, socket_port, midi_mode, match_device
#     file = open(settings_file)
#     settings = json.loads(file.read())
#     file.close()
#
#     keyMapFile = settings['keymap']
#     defaultInput = settings['default_input']
#     defaultOutput = settings['default_output']
#     ignoreInputs = settings['hide_inputs']
#     ignoreOutputs = settings['hide_outputs']
#     socket_port = settings['socket_port']
#     midi_mode = settings['midi_mode']
#     match_device = settings['match_device']
#     filterInput.clear()
#     filterInput.append(defaultInput)
#
# def read_settings(settings_file):
#     file = open(settings_file)
#     settings = json.loads(file.read())
#     file.close()
#     return settings
#
# def save_settings(settings_file, new_settings):
#     settings = new_settings
#     settings['last_input'] = filterInput
#     settings['last_output'] = activeOutput
#     settings['last_keymap'] = keyMapFile
#
#     settingsCLASS.last_input = filterInput
#     settingsCLASS.last_output = activeOutput
#     settingsCLASS.last_keymap = keyMapFile
#     settingsCLASS.save_settings()
#
#     file = open(settings_file,'w')
#     file.write(json.dumps(settings))
#     file.close()
#     print('MIDI Settings Saved')

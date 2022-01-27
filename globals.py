import pwd
import sys
import os
import json
import getpass
import platform
import shutil
from gpiozero import RGBLED
from colorzero import Color
from dotenv import load_dotenv
from multiprocessing import Queue
from cryptography.fernet import Fernet
sys.path.insert(0, '/usr/lib/python3/dist-packages')


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
    path2key = f'/home/{user}/.ssh/'

if not os.path.exists(path2key):
    os.makedirs(path2key)

# dummyLED if no GPIO available
class dummyLED():
    def __init__(self):
        pass
    def Color(colorName):
        pass
    def pulse(self,a,b,**kwargs):
        pass
    def blink(self,a,b,**kwargs):
        pass
    def on(self):
        pass
    def off(self):
        pass

# RaspberryPI gpio LED
class customRGBLED(RGBLED):
    def __init__(self, RedPin, GreenPin, BluePin):
        # attempt to create RGBLED object on GPIO pins
        try:
            super().__init__(RedPin,GreenPin,BluePin)
            self.light = self
        # if fail i.e. device has no GPIO pins, like a desktop
        except Exception as err:
            print(f'!! {err} !!')
            self.light = dummyLED()
    def blue(self):
        self.light.color = Color('blue')
    def green(self):
        self.light.color = Color('green')
    def red(self):
        self.light.color = Color('red')
    def yellow(self):
        self.light.color = Color('yellow')
    def orange(self):
        self.light.color = Color('orange')
    def customColor(self, color):
        self.light.color = Color(color)
    def blinkFast(self, color):
        self.light.blink(.25, .25, on_color=Color(color))
    def blinkSlow(self, color):
        self.light.blink(.5, .5, on_color=Color(color))
    def pulseSlow(self, color):
        self.light.pulse(2,2, on_color=Color(color), background=True)
    def pulseFast(self, color):
        self.light.pulse(.75, .75, on_color=Color(color), background=True)



led1 = customRGBLED(17,27,22)

############## GLOBAL FUNCTIONS ###############

#####  Crypto \\\\\\\\\\\\\\
def genwrite_key():
    key = Fernet.generate_key()
    with open (f'{path2key}midiMapper.key', 'wb') as key_file:
        key_file.write(key)

def call_key():
    try:
        return open(f'{path2key}midiMapper.key', 'rb').read()
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
    elif len(password) == 0:
        return [False,False]
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
class socketioMessage_Class():
    def __init__(self):
        self.handle = ''
        self.data = ''
        pass
    def send(self, handle, data):
        self.handle = handle
        self.data = data
        socketioMessageQueue.put(vars(self))

socketioMessage = socketioMessage_Class()

class SettingsManager:
    def __init__(self, file):
        self.filename = file
        self.config = {}

        for i in range(0,2):
            try:
                with open(self.filename) as config:
                    self.config = json.load(config)
                    print('SettingsManager: SettingsManager Init')
                    break
            except FileNotFoundError:
                shutil.copy('settings.template', 'settings.json')
                print(i)
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
        if not encryptedPwd[0] and encryptedPwd[1]:
            self.mqtt_paswd = encryptedPwd[1].decode('utf-8')
        self.config['mqtt_paswd'] = self.mqtt_paswd

        with open(self.filename, 'w') as config_file:
            json.dump(self.config, config_file, indent=4)
            # , indent=4
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
        if not encryptedPwd[0] and encryptedPwd[1]:
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
            json.dump(vars(self), file, indent=4)

    def write(self):
        with open(self.tempFile, 'w') as file:
            json.dump(vars(self), file, indent=4)

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

#edit_json.py

import json
import os

from modules.logger import *
from globals import *

def listKeyMaps():
    keymaps = os.listdir(f'{os.getcwd()}/keymaps')
    return keymaps

def loadKeyMap(keyMapFile):
    global map, message_buffer
    try:
        mapfile = open(f'./keymaps/{keyMapFile}')
        map = json.loads(mapfile.read())
        mapfile.close()
    except Exception as err:
        print(f'Error loading keymap - {err}')
        logging.error(f'Error loading keymap - {err}')
        # message_buffer.append(f'Error loading keymap - {err}')
        map = False
    activeSettings.setValue('keyMapFile', keyMapFile)
    return map

def getMappedKeys(key_map):
    global mappedkeys
    tempKeys = loadKeyMap(key_map)
    mappedkeys = tempKeys
    activeSettings.setValue('keymap', loadKeyMap(key_map))
    return mappedkeys

def searchKeyMap(mappedkeys, device, note, exact):
    if map:
        print(f'searching keymap for note {note} on {device}')
        for key in mappedkeys:
            if exact:
                device = device
            else:
                device = key['input_device']
            if (str(key['note']) == str(note)) and (key['input_device'] == device):
                return key

def getKeyMapIndex(current_keys, new_map):
    index = 0
    for key in current_keys:
        if (str(key['note']) == str(new_map['note'])) and (key['input_device'] == new_map['input_device']):
            return index
        index += 1

def newKeyMap(keyMapFile):
    fileName = f'{keyMapFile}.json'
    existing = listKeyMaps()
    if fileName in existing:
        return False
    else:
        f = open(f'./keymaps/{fileName}', 'w')
        f.write('[]')
        f.close()
        return True

def saveKeymap(keyMapFile, map):
    try:
        f = open(f'./keymaps/{keyMapFile}','w')
        f.write(map)
        f.close()
    except Exception as err:
        print(f'Error loading keymap - {err}')
        logging.error(f'Error loading keymap - {err}')
        # message_buffer.append(f'Error loading keymap - {err}')

def add_keymap(mapfile, new_map):
    current_keys = getMappedKeys(mapfile)
    current_keys.append(new_map)
    saveKeymap(mapfile, json.dumps(current_keys))

def del_keymap(mapfile, note, device):
    new_map={}
    new_map['note'] = note
    new_map['input_device'] = device
    try:
        current_keys = getMappedKeys(mapfile)
        current_keys.pop(getKeyMapIndex(current_keys, new_map))
        saveKeymap(mapfile, json.dumps(current_keys))
    except TypeError as err:
        logging.error(f'Error deleting mapped key - {err}')
    except Exception as err:
        logging.error(f'Error deleting mapped key - {err}')

def modify_keymap(mapfile, new_map):
    current_keys = getMappedKeys(mapfile)
    getKeyMapIndex(current_keys, new_map)
    current_keys[getKeyMapIndex(current_keys, new_map)] = new_map
    saveKeymap(mapfile, json.dumps(current_keys))

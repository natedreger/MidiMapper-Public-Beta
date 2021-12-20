#edit_json.py

import json

from logger import *
from globals import *


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
    return map

def getMappedKeys(key_map):
    global mappedkeys
    tempKeys = loadKeyMap(key_map)
    mappedkeys = tempKeys
    return mappedkeys

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

def del_keymap():
    pass

def modify_keymap():
    pass

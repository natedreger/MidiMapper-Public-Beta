#!/usr/bin/env python

# Help from https://github.com/alwaysai/video-streamer on  client-server setup

# web_interface.py

from flask_socketio import SocketIO
from flask import Flask, render_template, request
import json

app = Flask(__name__)
socketio = SocketIO(app)


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode, \
                            availableInputs=availableInputs, availableOutputs=availableOutputs,\
                            activeOutput=activeOutput, activeInput=activeInput)

@app.route('/settings')
def settings():
    return render_template('settings.html', async_mode=socketio.async_mode, \
                            availableInputs=availableInputs, availableOutputs=availableOutputs,\
                            activeOutput=activeOutput, activeInput=activeInput)

@app.route('/keymap')
def keymap():
    return render_template('keymap.html', async_mode=socketio.async_mode, \
                            availableInputs=availableInputs, availableOutputs=availableOutputs,\
                            activeOutput=activeOutput, activeInput=activeInput)


################## APP SOCKETS ################################
@socketio.on('connect')
def connect_web():
    print('[INFO] Web client connected: {}'.format(request.sid))


@socketio.on('disconnect')
def disconnect_web():
    print('[INFO] Web client disconnected: {}'.format(request.sid))


@socketio.on('connect')
def connect_midi():
    socketio.emit('my_response', {'data': f'Client {request.sid} Connected', 'count': 0})
    print('[INFO] client connected: {}'.format(request.sid))

@socketio.on('disconnect')
def disconnect_midi():
    socketio.emit('my_response', {'data': 'Disonnected', 'count': 0})
    print('[INFO] client disconnected: {}'.format(request.sid))

@socketio.on('*')
def catch_all(event, data):
    socketio.emit('my_response', {'data': f'{event} {data}', 'count': 0})
    print(f'[CATCH_ALL] {event} {data}')

@socketio.on('get_settings')
def get_settings(data):
    load_settings(settingsFile)
    socketio.emit('settings', {'availableInputs':availableInputs, 'availableOutputs':availableOutputs, \
                    'activeInput':activeInput, 'activeOutput':activeOutput, 'settings':settings, 'keymap':keymap})

@socketio.on('save_settings')
def save_settings(data):
    saveSettings(data, settingsFile)
    socketio.emit('save_settings',)

################# forward midi_mapper to web interface ######################3
@socketio.on('client_msg')
def client_msg(message):
    socketio.emit('my_response', {'data': message})

@socketio.on('setup')
def setup(message):
    global availableInputs, activeOutput, availableOutputs, activeInput, settings, keymap
    availableInputs = message['inputs']
    activeOutput = message['activeOutput']
    availableOutputs = message['outputs']
    activeInput = message['activeInput']
    settings = message['settings']
    keymap = message['keymap']
    socketio.emit('settings', {'availableInputs':availableInputs, 'availableOutputs':availableOutputs, \
                    'activeInput':activeInput, 'activeOutput':activeOutput, 'settings':settings, 'keymap':keymap})

@socketio.on('io_set')
def io_set(message):
    activeInput = message['data']['input']
    activeOutput = message['data']['output']
    socketio.emit('confirm_io', {'data': {'input':activeInput, 'output':activeOutput}})


#################### forward web_interface to midi_mapper ##################

@socketio.on('midi_msg')
def handle_midi_message(message):
    socketio.emit('midi_msg', {'data': message['data']})
    # print(message['data'])

@socketio.on('midi_sent')
def handle_midi_sent(message):
    socketio.emit('midi_sent', {'data': message['data']})
    # print(message['data'])

@socketio.on('midi_sent')
def handle_midi_sent(message):
    socketio.emit('midi_sent', {'data': message['data']})
    # print(message['data'])

@socketio.on('rescan_io')
def rescan_io():
    socketio.emit('rescan_io',)

@socketio.on('get_keymap')
def get_keymap():
    socketio.emit('reload_keymap',)

@socketio.on('apply_settings')
def apply_settings():
    socketio.emit('apply_settings',)

@socketio.event
def select_io(message):
    socketio.emit('select_io', {'data': message['data']})

@socketio.event
def webMidiNoteIn(message):
    socketio.emit('webMidiNoteIn', {'data': message['data']})

@socketio.event
def webPCIn(message):
    socketio.emit('webPCIn', {'data': message['data']})

################ Main Functions ###################################

def load_settings(settings_file):
    global settings, socket_port, settingsFile
    settingsFile = settings_file
    file = open(settings_file)
    settings = json.loads(file.read())
    socket_port = settings['socket_port']
    file.close()

def saveSettings(data, settings_file):
    file = open(settings_file)
    settings = json.loads(file.read())
    settings['socket_port'] = data['socket_port']
    file.close()
    socketio.emit('my_response', {'data': 'Settings Saved'})
    print('Settings Saved')

def server_main(settings_file):
    load_settings(settings_file)
    print('Server Main')
    print('[INFO] Starting server at http://localhost:5005')
    socketio.run(app=app, host='0.0.0.0', port=socket_port)

if __name__ == "__main__":
    server_main()

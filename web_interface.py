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
    socketio.emit('my_response', {'data': 'Connected', 'count': 0})
    print('[INFO] client connected: {}'.format(request.sid))

@socketio.on('disconnect')
def disconnect_midi():
    socketio.emit('my_response', {'data': 'Disonnected', 'count': 0})
    print('[INFO] client disconnected: {}'.format(request.sid))

################# forward midi_mapper to web interface ######################3
@socketio.on('client_msg')
def client_msg(message):
    socketio.emit('my_response', {'data': message})

@socketio.on('setup')
def setup(message):
    global availableInputs, activeOutput, availableOutputs, activeInput
    availableInputs = message['inputs']
    activeOutput = message['activeOutput']
    availableOutputs = message['outputs']
    activeInput = message['activeInput']
    settings = message['settings']
    keymap = message['keymap']

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

@socketio.event
def select_io(message):
    socketio.emit('select_io', {'data': message['data']})

@socketio.event
def webMidiNoteIn(message):
    socketio.emit('webMidiNoteIn', {'data': message['data']})

@socketio.event
def webPCIn(message):
    socketio.emit('webPCIn', {'data': message['data']})

def load_settings(settings_file):
    global settings, socket_port
    file = open(settings_file)
    settings = json.loads(file.read())
    socket_port = settings['socket_port']
    file.close()


def server_main(settings_file):
    load_settings(settings_file)
    print('Server Main')
    print('[INFO] Starting server at http://localhost:5005')
    socketio.run(app=app, host='0.0.0.0', port=socket_port)

if __name__ == "__main__":
    server_main()

# Help from https://github.com/alwaysai/video-streamer on  client-server setup

from flask_socketio import SocketIO
from flask import Flask, render_template, request

app = Flask(__name__)
socketio = SocketIO(app)


@app.route('/')
def index():
    """Home page."""
    # return render_template('index.html')
    return render_template('index.html', async_mode=socketio.async_mode, availableInputs=availableInputs, availableOutputs=availableOutputs, activeOutput=activeOutput)

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

@socketio.on('outports')
def send_outports(message):
    global availableOutputs
    availableOutputs = message['data']
    print(message['data'])

@socketio.on('output')
def send_output(message):
    global activeOutput
    activeOutput = message['data']
    print(message['data'])

@socketio.on('inports')
def send_inputs(message):
    global availableInputs
    availableInputs = message['data']
    print(message['data'])

@socketio.on('midi_msg')
def handle_midi_message(message):
    socketio.emit('midi_msg', {'data': message['data']})
    print(message['data'])

@socketio.on('midi_sent')
def handle_midi_sent(message):
    socketio.emit('midi_sent', {'data': message['data']})
    print(message['data'])

@socketio.event
def webMidiNoteIn(message):
    socketio.emit('webMidiNoteIn', {'data': message['data']})

@socketio.event
def webPCIn(message):
    socketio.emit('webPCIn', {'data': message['data']})

def server_main():
    print('Server Main')
    print('[INFO] Starting server at http://localhost:5005')
    socketio.run(app=app, host='0.0.0.0', port=5005)

if __name__ == "__main__":
    server_main()

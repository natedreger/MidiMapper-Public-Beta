import threading
from pythonosc import udp_client
from globals import streamDeckQueue, publishQueue, ledQueue, socketioMessage

def streamDeckQueueListener():
    while True:
        sd = streamDeckQueue.get(1)
        if sd['command_type'] == 'MIDI':
            print(f"MIDI: {sd['command_string']}")
            midi = list(sd['command_string'].split(","))
            if int(midi[0]) <= 16:
                midi[0] = int(midi[0]) + 143
            else: midi[0] = int(midi[0])
            midi[1] = int(midi[1])
            midi[2] = int(midi[2])
            device = 'StreamDeck'
            print(device, midi)

        elif sd['command_type'] == 'OSC':
            print(f"OSC: {sd['command_string']}")
            addr = sd['command_string'].split('/')
            host_port = addr.pop(0)
            host_port = host_port.split(':')
            host = host_port.pop(0)
            port = int(host_port.pop(0))
            message = '/'
            message = '/'+message.join(addr)
            try:
                OSC_client = udp_client.SimpleUDPClient(host, port)
                print(host,port)
                OSC_client.send_message(message,'')
                print(f'OSC message {message}')
                socketioMessage.send('midi_sent', {'data': f"OSC message {host}:{port}{message}"})
                ledQueue.put('led1.orange()')
            except Exception as err:
                print(err)
                socketioMessage.send('client_msg', f"Error: {host}{port} {err}")
            print(host,port,message)

        elif sd['command_type'] == 'MQTT':
            print(f"MQTT: {sd['command_string']}")
            addr = sd['command_string'].split('/')
            topic = addr.pop(0)
            message = '/'
            message = '/'+message.join(addr)
            publishQueue.put([topic, message])
            print(f"MQTT topic {topic} message {message}")
            socketioMessage.send('midi_sent', {'data': f"Sent to MQTT topic {topic} message {message}"})
            ledQueue.put('led1.orange()')
            print(topic, message)

sdListen = threading.Thread(target=streamDeckQueueListener)
sdListen.start()

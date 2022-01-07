import socketio
import os


from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

from modules.logger import *
from midi_mapper import q
from globals import connectSocket, owner, settingsCLASS


oscSocket = socketio.Client()

def osc_handler(address, *args):
    print(address)
    parseOSC(address, *args)
    oscSocket.emit('incomingOSC', address)


def parseOSC(address, *args):
    # address = '/MIDI/NOTE_ON/1/55'
    # address = '/OSC/kampkrusty.local/8000/app/QLab/activate'

    addr = address.split('/')
    addr.pop(0)

    if addr[0] == 'MIDI' or 'OSC':
        processOSC(addr)
    else:
        pass

class oscMIDImessage():
    pass

def processOSC(addr):
    if addr[0] == 'MIDI':
        device = 'OSC2MIDI'
        type = addr[1]
        ch = int(addr[2]) + 143
        note = int(addr[3])
        oscSocket.emit('OSC2MIDI_out', [device,[ch,note,1],type])
    elif addr[0] == 'OSC':
        destination = addr[1]
        dest_port = addr[2]
        del addr[:3]
        message = '/'
        message = f'/{message.join(addr)}'
        OSC_client = udp_client.SimpleUDPClient(destination, int(dest_port))
        OSC_client.send_message(message,'')
        oscSocket.emit('outgoingOSC', f'{destination}:{dest_port}{message}')
    else:
        pass

dispatcher = Dispatcher()
dispatcher.set_default_handler(osc_handler)


def osc_main(settings):
    socket_addr = 'localhost'
    socket_port = int(settingsCLASS.socket_port)
    osc_ip = "0.0.0.0" #allow external
    osc_port = int(settingsCLASS.osc_port)#9001
    logs.debug(f'osc.py running as PID: {os.getpid()} as User: {owner(os.getpid())}')
    connectSocket(oscSocket, socket_addr, socket_port)
    server = BlockingOSCUDPServer((osc_ip, osc_port), dispatcher)
    print(f"OSC Listening on {osc_ip}:{osc_port}")
    server.serve_forever()  # Blocks forever
    server.shutdown()

if __name__ == '__main__':
    settings={}
    settings['socket_port'] = 5005
    osc_main(settings)
